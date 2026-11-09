from unittest import mock

import httpx
import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from apps.notifications.events import SmsEvent, placeholders, to_pattern_text
from apps.notifications.models import SmsLog, SmsProvider, SmsSettings, SmsTemplate
from apps.notifications.providers import SmsError
from apps.notifications.services import send_now
from apps.notifications.tasks import send_event_sms
from apps.orders.models import Order, OrderStatus
from apps.payments.models import Payment

from .test_orders_payments import checkout

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _send_sms_inline():
    """Run the Celery task right away, whatever CELERY_TASK_ALWAYS_EAGER says."""
    with mock.patch.object(send_event_sms, "delay", side_effect=lambda *args: send_event_sms.apply(args=args)):
        yield


def soap_reply(value: str) -> httpx.Response:
    body = (
        '<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">'
        '<soap:Body><SendByBaseNumberResponse xmlns="http://tempuri.org/">'
        f"<SendByBaseNumberResult>{value}</SendByBaseNumberResult></SendByBaseNumberResponse></soap:Body></soap:Envelope>"
    )
    return httpx.Response(200, text=body)


def use_melipayamak():
    SmsTemplate.objects.update(body_id=1000)
    config = SmsSettings.load()
    config.provider, config.username, config.password = SmsProvider.MELIPAYAMAK, "shop", "secret"
    config.full_clean()
    config.save()


def test_named_variables_become_numbered_pattern():
    text = "{name} عزیز، سفارش {order_number} ثبت شد. {name}"
    assert placeholders(text) == ["name", "order_number"]
    assert to_pattern_text(text) == "{0} عزیز، سفارش {1} ثبت شد. {0}"


def test_every_event_has_a_template_and_only_login_and_payment_are_on_by_default():
    active = set(SmsTemplate.objects.filter(is_active=True).values_list("event", flat=True))
    assert SmsTemplate.objects.count() == len(SmsEvent.choices)
    assert active == {SmsEvent.OTP, SmsEvent.ORDER_PAID}
    assert SmsSettings.load().provider == SmsProvider.CONSOLE


def test_otp_is_logged_without_the_code(api_client, django_capture_on_commit_callbacks):
    with django_capture_on_commit_callbacks(execute=True):
        response = api_client.post("/api/auth/otp/request/", {"phone": "09121112233"}, format="json")
    assert response.status_code == 200
    log = SmsLog.objects.get(event=SmsEvent.OTP)
    assert log.status == SmsLog.Status.SENT and log.phone == "09121112233"
    assert log.text == "کد ورود شما به کرامت: *****"


def test_template_rejects_unknown_variables_and_disabling_login():
    template = SmsTemplate.objects.get(event=SmsEvent.ORDER_SHIPPED)
    template.text = "سفارش {order_number} با کد {code}"
    with pytest.raises(ValidationError, match="code"):
        template.full_clean()
    otp = SmsTemplate.objects.get(event=SmsEvent.OTP)
    otp.is_active = False
    with pytest.raises(ValidationError):
        otp.full_clean()


def test_melipayamak_needs_login_and_pattern_codes():
    config = SmsSettings.load()
    config.provider = SmsProvider.MELIPAYAMAK
    with pytest.raises(ValidationError, match="نام کاربری"):
        config.full_clean()
    config.username, config.password = "shop", "secret"
    with pytest.raises(ValidationError, match="کد پترن"):
        config.full_clean()


def test_melipayamak_sends_values_in_pattern_order():
    use_melipayamak()
    with mock.patch("apps.notifications.providers.httpx.post", return_value=soap_reply("1234567890123456789")) as post:
        log = send_now(
            SmsEvent.ORDER_PAID, "09121112233", {"name": "علی", "products": "شلوار", "order_number": "1405-1"}
        )
    body = post.call_args.kwargs["content"].decode()
    assert "<username>shop</username><password>secret</password>" in body
    assert "<text><string>علی</string><string>شلوار</string><string>1405-1</string></text>" in body
    assert "<to>09121112233</to><bodyId>1000</bodyId>" in body
    assert log.status == SmsLog.Status.SENT and log.detail == "1234567890123456789"


def test_melipayamak_error_is_logged_in_persian():
    use_melipayamak()
    with mock.patch("apps.notifications.providers.httpx.post", return_value=soap_reply("-4")):
        with pytest.raises(SmsError):
            send_now(SmsEvent.ORDER_PAID, "09121112233", {"name": "علی"})
    log = SmsLog.objects.get()
    assert log.status == SmsLog.Status.FAILED
    assert "تأیید نشده" in log.detail


def test_paid_order_sends_the_purchase_sms(
    auth_client, api_client, variant, address, shipping, django_capture_on_commit_callbacks
):
    order = checkout(auth_client, variant, address, shipping).json()
    start = auth_client.post("/api/payments/start/", {"order_id": order["id"]}, format="json").json()
    authority = Payment.objects.get(pk=start["payment_id"]).authority
    with django_capture_on_commit_callbacks(execute=True):
        verified = api_client.get(f"/api/payments/verify/?Authority={authority}&Status=OK")
    assert verified.json()["status"] == "success", (verified.json(), list(SmsLog.objects.values()))
    log = SmsLog.objects.get(event=SmsEvent.ORDER_PAID)
    assert f"خرید {variant.product.title} با موفقیت انجام شد" in log.text
    assert order["number"] in log.text


def test_admin_status_change_sends_sms_only_when_switched_on(
    client, auth_client, variant, address, shipping, django_capture_on_commit_callbacks
):
    client.force_login(get_user_model().objects.create_superuser("09120000000", "password"))
    order = Order.objects.get(pk=checkout(auth_client, variant, address, shipping).json()["id"])
    Order.objects.filter(pk=order.pk).update(status=OrderStatus.PAID, tracking_code="ABC123")
    url = "/admin/orders/order/"

    with django_capture_on_commit_callbacks(execute=True):
        client.post(url, {"action": "mark_shipped", "_selected_action": [order.pk]})
    assert not SmsLog.objects.filter(event=SmsEvent.ORDER_SHIPPED).exists()  # off by default

    SmsTemplate.objects.filter(event=SmsEvent.ORDER_SHIPPED).update(is_active=True)
    Order.objects.filter(pk=order.pk).update(status=OrderStatus.PAID)
    with django_capture_on_commit_callbacks(execute=True):
        client.post(url, {"action": "mark_shipped", "_selected_action": [order.pk]})
    log = SmsLog.objects.get(event=SmsEvent.ORDER_SHIPPED)
    assert "کد رهگیری مرسوله: ABC123" in log.text


def test_admin_pages_open(client):
    client.force_login(get_user_model().objects.create_superuser("09120000000", "password"))
    template = SmsTemplate.objects.get(event=SmsEvent.ORDER_PAID)
    page = client.get(f"/admin/notifications/smstemplate/{template.pk}/change/").content.decode()
    assert "{0} عزیز، خرید {1} با موفقیت انجام شد. شماره سفارش: {2}" in page
    assert client.get("/admin/notifications/smssettings/1/change/").status_code == 200
    assert client.get("/admin/notifications/smslog/").status_code == 200
