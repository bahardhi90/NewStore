"""Payment flow: start -> redirect -> (frontend) -> verify. Verification is idempotent."""

import logging
from dataclasses import dataclass

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.core import messages as msg
from apps.core.exceptions import StoreError
from apps.notifications.services import notify_order
from apps.orders.models import Order, OrderStatus
from apps.orders.services import mark_order_paid

from .gateways import GatewayError, get_gateway
from .models import Payment, PaymentMethod, PaymentStatus

logger = logging.getLogger(__name__)


@dataclass
class StartedPayment:
    payment: Payment
    redirect_url: str


def _select_method(code: str | None, amount: int) -> PaymentMethod:
    """The requested method, or the first available one (e.g. "try again" after a failed payment)."""
    methods = [m for m in PaymentMethod.objects.available() if m.supports_amount(amount)]
    method = next((m for m in methods if m.code == code), None) if code else next(iter(methods), None)
    if method is None:
        raise StoreError(
            msg.PAYMENT_METHOD_UNAVAILABLE,
            "payment_method_unavailable",
            errors={"method": [msg.PAYMENT_METHOD_UNAVAILABLE]},
        )
    return method


def start_payment(user, order_id: int, method_code: str | None = None) -> StartedPayment:
    order = Order.objects.filter(pk=order_id, user=user).first()
    if order is None:
        raise StoreError(msg.NOT_FOUND, "not_found", status_code=404)
    if order.status != OrderStatus.PENDING or (order.expires_at and order.expires_at <= timezone.now()):
        raise StoreError(msg.ORDER_NOT_PAYABLE, "order_not_payable", errors={"order_id": [msg.ORDER_NOT_PAYABLE]})

    gateway = get_gateway(_select_method(method_code, order.total).code)
    payment = Payment.objects.create(order=order, amount=order.total, gateway=gateway.name)
    try:
        result = gateway.start(
            amount_toman=order.total,
            description=f"سفارش {order.number}",
            callback_url=settings.PAYMENT_CALLBACK_URL,
            mobile=user.phone,
            order_number=order.number,
            order=order,
        )
    except GatewayError as exc:
        logger.warning("Gateway start failed for order %s: %s", order.number, exc)
        payment.status = PaymentStatus.FAILED
        payment.raw_request = {"error": str(exc)}
        payment.save(update_fields=["status", "raw_request", "updated_at"])
        raise StoreError(msg.GATEWAY_ERROR, "gateway_error", status_code=502) from exc

    payment.authority = result.authority
    payment.raw_request = result.raw
    payment.save(update_fields=["authority", "raw_request", "updated_at"])
    return StartedPayment(payment=payment, redirect_url=result.redirect_url)


def _result(payment: Payment) -> dict:
    order = payment.order
    if payment.status == PaymentStatus.SUCCESS:
        detail = msg.PAYMENT_ORDER_EXPIRED if payment.needs_refund else msg.PAYMENT_SUCCESS
        status = "failed" if payment.needs_refund else "success"
    elif payment.status == PaymentStatus.CANCELLED:
        detail, status = msg.PAYMENT_CANCELLED, "cancelled"
    else:
        detail, status = msg.PAYMENT_FAILED, "failed"
    return {
        "status": status,
        "detail": detail,
        "order_id": order.id,
        "order_number": order.number,
        "ref_id": payment.ref_id or None,
        "amount": payment.amount,
    }


def verify_payment(authority: str, gateway_status: str, tracking_code: str = "", purchase_type: str = "") -> dict:
    with transaction.atomic():
        payment = Payment.objects.select_for_update().select_related("order").filter(authority=authority).first()
        if payment is None:
            raise StoreError(msg.NOT_FOUND, "not_found", status_code=404)

        if payment.status != PaymentStatus.INITIATED:  # idempotent: second call returns the stored result
            return _result(payment)

        if (gateway_status or "").upper() != "OK":
            payment.status = PaymentStatus.CANCELLED
            payment.raw_response = {"status": gateway_status}
            payment.save(update_fields=["status", "raw_response", "updated_at"])
            return _result(payment)

        order = Order.objects.select_for_update().get(pk=payment.order_id)
        if payment.amount != order.total:
            payment.status = PaymentStatus.FAILED
            payment.raw_response = {"error": "amount_mismatch", "order_total": order.total}
            payment.save(update_fields=["status", "raw_response", "updated_at"])
            logger.error("Amount mismatch for payment %s", payment.pk)
            return {**_result(payment), "detail": msg.PAYMENT_AMOUNT_MISMATCH}

        context = {
            "order": order,
            "start_response": payment.raw_request,
            "tracking_code": tracking_code,
            "purchase_type": purchase_type,
        }
        try:
            result = get_gateway(payment.gateway).verify(
                authority=authority, amount_toman=payment.amount, context=context
            )
        except GatewayError as exc:
            logger.warning("Gateway verify failed for %s: %s", authority, exc)
            raise StoreError(msg.GATEWAY_ERROR, "gateway_error", status_code=502) from exc

        payment.raw_response = result.raw
        payment.verified_at = timezone.now()
        if not result.success:
            payment.status = PaymentStatus.FAILED
            payment.save(update_fields=["status", "raw_response", "verified_at", "updated_at"])
            return _result(payment)

        payment.status = PaymentStatus.SUCCESS
        payment.ref_id = result.ref_id
        payment.card_pan = result.card_pan
        fulfilled = mark_order_paid(order)
        payment.needs_refund = not fulfilled
        payment.save()

        if fulfilled:
            notify_order(order)
        payment.order = order
        return _result(payment)
