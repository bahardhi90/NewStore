from datetime import timedelta
from unittest import mock

import pytest
from django.utils import timezone

from apps.catalog.models import Variant
from apps.orders.models import Order, OrderStatus
from apps.orders.services import cancel_expired_orders
from apps.payments.gateways import GatewayError, VerifyResult
from apps.payments.models import Payment, PaymentStatus

from .factories import AddressFactory, ShippingMethodFactory, VariantFactory

pytestmark = pytest.mark.django_db


def checkout(client, variant, address, shipping, quantity=2):
    client.post("/api/cart/items/", {"variant_id": variant.id, "quantity": quantity}, format="json")
    return client.post("/api/orders/", {"address_id": address.id, "shipping_method_id": shipping.id}, format="json")


def test_create_order_reserves_stock_and_snapshots(auth_client, variant, address, shipping):
    response = checkout(auth_client, variant, address, shipping)
    assert response.status_code == 201, response.json()
    order = response.json()
    assert order["status"] == "pending"
    assert order["status_display"] == "در انتظار پرداخت"
    assert order["subtotal"] == 4_000_000
    assert order["discount_total"] == 800_000
    assert order["shipping_cost"] == 60_000
    assert order["total"] == 3_260_000
    assert order["number"].count("-") == 1
    assert order["address"]["city"] == "تهران"
    assert order["items"][0]["final_unit_price"] == 1_600_000
    variant.refresh_from_db()
    assert variant.stock == 3
    assert auth_client.get("/api/cart/").json()["items"] == []

    # price change after purchase does not change the order
    variant.product.base_price = 9_000_000
    variant.product.save()
    detail = auth_client.get(f"/api/me/orders/{order['id']}/").json()
    assert detail["total"] == 3_260_000


def test_free_shipping(auth_client, variant, address):
    free = ShippingMethodFactory(cost=60_000, free_over=1_000_000)
    order = checkout(auth_client, variant, address, free).json()
    assert order["shipping_cost"] == 0


def test_empty_cart(auth_client, address, shipping):
    response = auth_client.post(
        "/api/orders/", {"address_id": address.id, "shipping_method_id": shipping.id}, format="json"
    )
    assert response.status_code == 400
    assert response.json()["code"] == "cart_empty"


def test_stock_changed_before_checkout(auth_client, variant, address, shipping):
    auth_client.post("/api/cart/items/", {"variant_id": variant.id, "quantity": 3}, format="json")
    Variant.objects.filter(pk=variant.pk).update(stock=1)
    response = auth_client.post(
        "/api/orders/", {"address_id": address.id, "shipping_method_id": shipping.id}, format="json"
    )
    assert response.status_code == 409
    assert response.json()["code"] == "out_of_stock"


def test_other_users_address_rejected(auth_client, variant, shipping):
    other = AddressFactory(user__phone="09128888888")
    auth_client.post("/api/cart/items/", {"variant_id": variant.id, "quantity": 1}, format="json")
    response = auth_client.post(
        "/api/orders/", {"address_id": other.id, "shipping_method_id": shipping.id}, format="json"
    )
    assert response.status_code == 400
    assert "address_id" in response.json()["errors"]


def test_my_orders_list_and_owner_only(auth_client, api_client, variant, address, shipping):
    order = checkout(auth_client, variant, address, shipping).json()
    listing = auth_client.get("/api/me/orders/").json()
    assert listing["count"] == 1
    assert auth_client.get("/api/me/orders/?status=paid").json()["count"] == 0

    from rest_framework_simplejwt.tokens import RefreshToken

    from .factories import UserFactory

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(UserFactory()).access_token}")
    assert api_client.get(f"/api/me/orders/{order['id']}/").status_code == 404


def test_auto_cancel_releases_stock(auth_client, variant, address, shipping):
    order = checkout(auth_client, variant, address, shipping).json()
    Order.objects.filter(pk=order["id"]).update(expires_at=timezone.now() - timedelta(minutes=1))
    assert cancel_expired_orders() == 1
    variant.refresh_from_db()
    assert variant.stock == 5
    assert Order.objects.get(pk=order["id"]).status == OrderStatus.CANCELLED
    assert cancel_expired_orders() == 0  # idempotent
    variant.refresh_from_db()
    assert variant.stock == 5


def test_payment_success_flow_is_idempotent(
    auth_client, api_client, variant, address, shipping, django_capture_on_commit_callbacks
):
    order = checkout(auth_client, variant, address, shipping).json()
    start = auth_client.post("/api/payments/start/", {"order_id": order["id"]}, format="json")
    assert start.status_code == 200
    redirect_url = start.json()["redirect_url"]
    assert redirect_url.startswith("http://localhost:3000/payment/result?Authority=")
    authority = Payment.objects.get(pk=start.json()["payment_id"]).authority

    with (
        mock.patch("apps.notifications.tasks.send_event_sms.delay") as sms,
        django_capture_on_commit_callbacks(execute=True),
    ):
        first = api_client.get(f"/api/payments/verify/?Authority={authority}&Status=OK")
    assert first.status_code == 200
    assert first.json()["status"] == "success"
    assert first.json()["ref_id"]
    sms.assert_called_once()

    with mock.patch("apps.payments.gateways.fake.FakeGateway.verify") as verify:
        second = api_client.get(f"/api/payments/verify/?Authority={authority}&Status=OK")
        verify.assert_not_called()
    assert second.json() == first.json()

    order_obj = Order.objects.get(pk=order["id"])
    assert order_obj.status == OrderStatus.PAID
    variant.product.refresh_from_db()
    assert variant.product.sales_count == 2
    # paid order can not be paid again
    again = auth_client.post("/api/payments/start/", {"order_id": order["id"]}, format="json")
    assert again.json()["code"] == "order_not_payable"


def test_payment_cancelled_by_user(auth_client, api_client, variant, address, shipping):
    order = checkout(auth_client, variant, address, shipping).json()
    start = auth_client.post("/api/payments/start/", {"order_id": order["id"]}, format="json").json()
    authority = Payment.objects.get(pk=start["payment_id"]).authority
    body = api_client.get(f"/api/payments/verify/?Authority={authority}&Status=NOK").json()
    assert body["status"] == "cancelled"
    assert Order.objects.get(pk=order["id"]).status == OrderStatus.PENDING
    # the user can retry
    assert auth_client.post("/api/payments/start/", {"order_id": order["id"]}, format="json").status_code == 200


def test_payment_verify_failed_by_gateway(auth_client, api_client, variant, address, shipping):
    order = checkout(auth_client, variant, address, shipping).json()
    start = auth_client.post("/api/payments/start/", {"order_id": order["id"]}, format="json").json()
    authority = Payment.objects.get(pk=start["payment_id"]).authority
    with mock.patch("apps.payments.gateways.fake.FakeGateway.verify", return_value=VerifyResult(success=False)):
        body = api_client.get(f"/api/payments/verify/?Authority={authority}&Status=OK").json()
    assert body["status"] == "failed"
    assert Payment.objects.get(authority=authority).status == PaymentStatus.FAILED


def test_payment_gateway_down_can_retry_verify(auth_client, api_client, variant, address, shipping):
    order = checkout(auth_client, variant, address, shipping).json()
    start = auth_client.post("/api/payments/start/", {"order_id": order["id"]}, format="json").json()
    authority = Payment.objects.get(pk=start["payment_id"]).authority
    with mock.patch("apps.payments.gateways.fake.FakeGateway.verify", side_effect=GatewayError("timeout")):
        response = api_client.get(f"/api/payments/verify/?Authority={authority}&Status=OK")
    assert response.status_code == 502
    assert response.json()["code"] == "gateway_error"
    assert api_client.get(f"/api/payments/verify/?Authority={authority}&Status=OK").json()["status"] == "success"


def test_payment_after_auto_cancel_restocks_if_possible(auth_client, api_client, variant, address, shipping):
    order = checkout(auth_client, variant, address, shipping).json()
    start = auth_client.post("/api/payments/start/", {"order_id": order["id"]}, format="json").json()
    authority = Payment.objects.get(pk=start["payment_id"]).authority
    Order.objects.filter(pk=order["id"]).update(expires_at=timezone.now() - timedelta(minutes=1))
    cancel_expired_orders()
    body = api_client.get(f"/api/payments/verify/?Authority={authority}&Status=OK").json()
    assert body["status"] == "success"
    variant.refresh_from_db()
    assert variant.stock == 3


def test_payment_after_auto_cancel_without_stock_needs_refund(auth_client, api_client, variant, address, shipping):
    order = checkout(auth_client, variant, address, shipping).json()
    start = auth_client.post("/api/payments/start/", {"order_id": order["id"]}, format="json").json()
    authority = Payment.objects.get(pk=start["payment_id"]).authority
    Order.objects.filter(pk=order["id"]).update(expires_at=timezone.now() - timedelta(minutes=1))
    cancel_expired_orders()
    Variant.objects.filter(pk=variant.pk).update(stock=0)
    body = api_client.get(f"/api/payments/verify/?Authority={authority}&Status=OK").json()
    assert body["status"] == "failed"
    assert Payment.objects.get(authority=authority).needs_refund is True


def test_unknown_authority(api_client):
    assert api_client.get("/api/payments/verify/?Authority=nope&Status=OK").status_code == 404


def test_shipping_methods_and_stores(api_client):
    from .factories import StoreFactory

    ShippingMethodFactory()
    StoreFactory()
    assert len(api_client.get("/api/shipping-methods/").json()) == 1
    assert api_client.get("/api/stores/").json()[0]["city"] == "تهران"


def test_reserved_stock_blocks_further_cart_adds(auth_client, address, shipping):
    v = VariantFactory(stock=2)
    first = checkout(auth_client, v, address, shipping, quantity=2)
    assert first.status_code == 201
    response = auth_client.post("/api/cart/items/", {"variant_id": v.id, "quantity": 1}, format="json")
    assert response.status_code == 409
    v.refresh_from_db()
    assert v.stock == 0
