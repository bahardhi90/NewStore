from unittest import mock

import httpx
import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.test import override_settings

from apps.orders.models import Order, OrderStatus
from apps.payments.admin import PaymentMethodForm
from apps.payments.models import Payment, PaymentCode, PaymentMethod, PaymentStatus

from .test_orders_payments import checkout

pytestmark = pytest.mark.django_db

CREDENTIALS = {"username": "shop", "password": "secret", "client_id": "cid", "client_secret": "csecret"}


@pytest.fixture(autouse=True)
def clean_cache():
    cache.clear()


@pytest.fixture
def admin_client(client):
    client.force_login(get_user_model().objects.create_superuser("09120000000", "password"))
    return client


def enable(code: str, **fields) -> PaymentMethod:
    PaymentMethod.objects.filter(code=code).update(is_active=True, **CREDENTIALS, **fields)
    return PaymentMethod.objects.get(code=code)


def json_response(body: dict, status: int = 200) -> httpx.Response:
    return httpx.Response(status, json=body, request=httpx.Request("POST", "https://gateway.test"))


def token_response() -> httpx.Response:
    return json_response({"access_token": "tok", "expires_in": 3600})


def start(client, order_id: int, method: str | None = None):
    payload = {"order_id": order_id, **({"method": method} if method else {})}
    return client.post("/api/payments/start/", payload, format="json")


def test_migration_seeds_every_method_with_installments_off():
    assert set(PaymentMethod.objects.values_list("code", flat=True)) == set(PaymentCode.values)
    assert not PaymentMethod.objects.get(code="digipay").is_active
    assert not PaymentMethod.objects.get(code="snapppay").is_active


def test_methods_endpoint_lists_only_active_and_hides_secrets(api_client):
    enable("digipay")
    body = api_client.get("/api/payments/methods/").json()
    assert [m["code"] for m in body] == ["digipay", "fake"]
    assert set(body[0]) == {"code", "title", "description", "logo", "min_amount", "max_amount"}


@override_settings(PAYMENT_GATEWAY="zarinpal")
def test_fake_gateway_is_never_available_outside_dev(api_client, auth_client, variant, address, shipping):
    assert api_client.get("/api/payments/methods/").json() == []
    order = checkout(auth_client, variant, address, shipping).json()
    response = start(auth_client, order["id"], "fake")
    assert response.status_code == 400
    assert response.json()["code"] == "payment_method_unavailable"
    assert not Payment.objects.exists()


def test_disabled_method_is_rejected(auth_client, variant, address, shipping):
    order = checkout(auth_client, variant, address, shipping).json()
    assert start(auth_client, order["id"], "digipay").json()["code"] == "payment_method_unavailable"


def test_amount_limits_are_enforced(auth_client, variant, address, shipping):
    enable("snapppay", min_amount=99_000_000)
    order = checkout(auth_client, variant, address, shipping).json()
    assert start(auth_client, order["id"], "snapppay").json()["code"] == "payment_method_unavailable"


def test_cannot_activate_without_credentials():
    method = PaymentMethod.objects.get(code="snapppay")
    method.is_active = True
    with pytest.raises(ValidationError):
        method.full_clean()


def test_admin_form_keeps_secret_when_left_blank():
    method = enable("digipay")
    data = {
        "code": method.code,
        "title": method.title,
        "order": method.order,
        "is_active": True,
        "username": "shop",
        "client_id": "cid",
        "password": "",
        "client_secret": "",
    }
    form = PaymentMethodForm(data, instance=method)
    assert form.is_valid(), form.errors
    saved = form.save()
    assert saved.password == "secret"
    assert saved.client_secret == "csecret"


@pytest.mark.parametrize("code", ["zarinpal", "digipay", "snapppay"])
def test_admin_pages_open_and_show_the_right_fields(admin_client, code):
    method = PaymentMethod.objects.get(code=code)
    assert admin_client.get("/admin/payments/paymentmethod/").status_code == 200
    page = admin_client.get(f"/admin/payments/paymentmethod/{method.pk}/change/")
    assert page.status_code == 200
    assert (b'name="client_secret"' in page.content) == (code != "zarinpal")
    assert (b'name="merchant_id"' in page.content) == (code == "zarinpal")


def test_admin_list_checkbox_refuses_method_without_credentials(admin_client):
    methods = list(PaymentMethod.objects.all())
    data = {
        "form-TOTAL_FORMS": len(methods),
        "form-INITIAL_FORMS": len(methods),
        "_save": "1",
    }
    target = next(m for m in methods if m.code == "snapppay")
    for i, method in enumerate(methods):
        data[f"form-{i}-id"] = method.pk
        data[f"form-{i}-order"] = method.order
        if method.is_active or method == target:
            data[f"form-{i}-is_active"] = "on"
    response = admin_client.post("/admin/payments/paymentmethod/", data)
    assert response.status_code == 200
    assert "ابتدا این موارد را تکمیل کنید" in response.content.decode()
    assert not PaymentMethod.objects.get(code="snapppay").is_active


def test_site_settings_admin_opens_without_add_or_delete(admin_client):
    assert admin_client.get("/admin/content/sitesettings/").status_code == 200
    assert admin_client.get("/admin/content/sitesettings/1/change/").status_code == 200
    assert admin_client.get("/admin/content/sitesettings/add/").status_code == 403
    assert admin_client.get("/admin/content/sitesettings/1/delete/").status_code == 403


def test_digipay_credit_purchase_is_verified_and_delivered(auth_client, api_client, variant, address, shipping):
    enable("digipay")
    order = checkout(auth_client, variant, address, shipping).json()

    ticket = {"result": {"status": 0}, "ticket": "t", "redirectUrl": "https://digipay.test/pay"}
    with (
        mock.patch("httpx.post", return_value=token_response()),
        mock.patch("httpx.request", return_value=json_response(ticket)) as request,
    ):
        response = start(auth_client, order["id"], "digipay")
    assert response.json()["redirect_url"] == "https://digipay.test/pay"
    sent = request.call_args.kwargs["json"]
    assert sent["amount"] == order["total"] * 10
    assert sent["cellNumber"] == Order.objects.get().user.phone
    assert sent["callbackUrl"].startswith("http://localhost:3000/api/payments/callback?authority=DP")
    assert request.call_args.kwargs["headers"]["Authorization"] == "Bearer tok"

    authority = Payment.objects.get().authority
    verified = {"result": {"status": 0}, "providerId": authority, "amount": order["total"] * 10, "rrn": "777"}
    with mock.patch(
        "httpx.request", side_effect=[json_response(verified), json_response({"result": {"status": 0}})]
    ) as request:
        url = f"/api/payments/verify/?Authority={authority}&Status=OK&TrackingCode=TC1&Type=13"
        body = api_client.get(url).json()
    assert body["status"] == "success"
    assert body["ref_id"] == "777"
    assert request.call_args_list[0].args[1].endswith("/purchases/verify")
    assert request.call_args_list[1].args[1].endswith("/purchases/deliver")
    assert Order.objects.get(pk=order["id"]).status == OrderStatus.PAID


def test_digipay_amount_mismatch_fails(auth_client, api_client, variant, address, shipping):
    enable("digipay")
    order = checkout(auth_client, variant, address, shipping).json()
    ticket = {"result": {"status": 0}, "redirectUrl": "https://digipay.test/pay"}
    with (
        mock.patch("httpx.post", return_value=token_response()),
        mock.patch("httpx.request", return_value=json_response(ticket)),
    ):
        start(auth_client, order["id"], "digipay")
    authority = Payment.objects.get().authority
    verified = {"result": {"status": 0}, "providerId": authority, "amount": 10}
    with mock.patch("httpx.request", return_value=json_response(verified)):
        url = f"/api/payments/verify/?Authority={authority}&Status=OK&TrackingCode=TC1&Type=11"
        body = api_client.get(url).json()
    assert body["status"] == "failed"
    assert Order.objects.get(pk=order["id"]).status == OrderStatus.PENDING


def start_snapppay(auth_client, variant, address, shipping) -> tuple[dict, dict, str]:
    enable("snapppay")
    order = checkout(auth_client, variant, address, shipping).json()
    token = {"successful": True, "response": {"paymentToken": "PT", "paymentPageUrl": "https://snapp.test/pay"}}
    with (
        mock.patch("httpx.post", return_value=token_response()),
        mock.patch("httpx.request", return_value=json_response(token)) as request,
    ):
        assert start(auth_client, order["id"], "snapppay").json()["redirect_url"] == "https://snapp.test/pay"
    return order, request.call_args.kwargs["json"], Payment.objects.get().authority


def test_snapppay_sends_rial_cart_and_settles(auth_client, api_client, variant, address, shipping):
    order, sent, authority = start_snapppay(auth_client, variant, address, shipping)
    cart = sent["cartList"][0]
    assert sent["amount"] == cart["totalAmount"] == order["total"] * 10
    assert sent["mobile"].startswith("+989")
    assert cart["shippingAmount"] == order["shipping_cost"] * 10
    items_total = sum(item["amount"] * item["count"] for item in cart["cartItems"])
    assert items_total + cart["shippingAmount"] == cart["totalAmount"]

    done = json_response({"successful": True, "response": {}})
    with mock.patch("httpx.request", return_value=done) as request:
        body = api_client.get(f"/api/payments/verify/?Authority={authority}&Status=OK").json()
    assert body["status"] == "success"
    assert [call.args[1].rsplit("/", 1)[1] for call in request.call_args_list] == ["verify", "settle"]
    assert Order.objects.get(pk=order["id"]).status == OrderStatus.PAID


def test_snapppay_settle_failure_can_be_retried(auth_client, api_client, variant, address, shipping):
    order, _, authority = start_snapppay(auth_client, variant, address, shipping)
    failed = json_response({"successful": False})
    verify_ok = json_response({"successful": True})
    status_verify = json_response({"successful": True, "response": {"status": "VERIFY"}})
    with mock.patch("httpx.request", side_effect=[verify_ok, failed, status_verify]):
        response = api_client.get(f"/api/payments/verify/?Authority={authority}&Status=OK")
    assert response.status_code == 502
    assert Payment.objects.get().status == PaymentStatus.INITIATED

    # verify can not run twice at SnappPay, so the retry continues from the reported status
    with mock.patch("httpx.request", side_effect=[failed, status_verify, json_response({"successful": True})]):
        body = api_client.get(f"/api/payments/verify/?Authority={authority}&Status=OK").json()
    assert body["status"] == "success"
    assert Order.objects.get(pk=order["id"]).status == OrderStatus.PAID


def test_rejected_credentials_surface_as_gateway_error(auth_client, variant, address, shipping):
    enable("snapppay")
    order = checkout(auth_client, variant, address, shipping).json()
    with mock.patch("httpx.post", return_value=json_response({"error": "invalid_grant"}, 401)):
        response = start(auth_client, order["id"], "snapppay")
    assert response.status_code == 502
    assert response.json()["code"] == "gateway_error"
    assert Payment.objects.get().status == PaymentStatus.FAILED


def test_expired_token_is_refreshed_once(auth_client, variant, address, shipping):
    enable("snapppay")
    cache.set("payments:token:snapppay", "stale")
    order = checkout(auth_client, variant, address, shipping).json()
    token = {"successful": True, "response": {"paymentToken": "PT", "paymentPageUrl": "https://snapp.test/pay"}}
    with (
        mock.patch("httpx.post", return_value=token_response()),
        mock.patch("httpx.request", side_effect=[json_response({}, 401), json_response(token)]) as request,
    ):
        assert start(auth_client, order["id"], "snapppay").status_code == 200
    assert request.call_args.kwargs["headers"]["Authorization"] == "Bearer tok"
