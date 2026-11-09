"""Order business logic: checkout, stock reservation, cancellation, payment confirmation."""

import logging
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from apps.accounts.models import Address
from apps.cart.models import Cart
from apps.catalog.models import Product, Variant
from apps.core import messages as msg
from apps.core.exceptions import StoreError
from apps.core.pricing import calc_final_price
from apps.core.utils import fa_digits, gregorian_to_jalali
from apps.notifications.services import notify_order

from .models import Order, OrderItem, OrderNumberSequence, OrderStatus, ShippingMethod

logger = logging.getLogger(__name__)


def next_order_number() -> str:
    """e.g. 1405-000123. Must be called inside a transaction."""
    today = timezone.localdate()
    year = gregorian_to_jalali(today.year, today.month, today.day)[0]
    seq, _ = OrderNumberSequence.objects.select_for_update().get_or_create(year=year)
    seq.last_value = F("last_value") + 1
    seq.save(update_fields=["last_value"])
    seq.refresh_from_db()
    return f"{year}-{seq.last_value:06d}"


@transaction.atomic
def create_order(user, *, address_id: int, shipping_method_id: int, note: str = "") -> Order:
    address = Address.objects.filter(pk=address_id, user=user).first()
    if address is None:
        raise StoreError(msg.ADDRESS_NOT_FOUND, "validation_error", errors={"address_id": [msg.ADDRESS_NOT_FOUND]})
    method = ShippingMethod.objects.filter(pk=shipping_method_id, is_active=True).first()
    if method is None:
        raise StoreError(
            msg.SHIPPING_NOT_FOUND, "validation_error", errors={"shipping_method_id": [msg.SHIPPING_NOT_FOUND]}
        )

    cart = Cart.objects.filter(user=user).first()
    cart_items = list(cart.items.all()) if cart else []
    if not cart_items:
        raise StoreError(msg.CART_EMPTY, "cart_empty")

    # Lock variants in a stable order to avoid deadlocks between concurrent checkouts.
    variant_ids = sorted({item.variant_id for item in cart_items})
    variants = {
        v.id: v for v in Variant.objects.select_for_update(of=("self",)).filter(id__in=variant_ids).order_by("id")
    }
    products = Product.objects.in_bulk({v.product_id for v in variants.values()})

    problems: list[str] = []
    for item in cart_items:
        variant = variants.get(item.variant_id)
        product = products.get(variant.product_id) if variant else None
        if variant is None or product is None or not product.is_active:
            problems.append(msg.PRODUCT_UNAVAILABLE)
            continue
        if item.quantity > variant.stock:
            reason = msg.SOLD_OUT if variant.stock == 0 else msg.ONLY_N_IN_STOCK.format(count=fa_digits(variant.stock))
            problems.append(
                msg.ITEM_OUT_OF_STOCK.format(title=product.title, size=variant.size, color=variant.color, reason=reason)
            )
    if problems:
        raise StoreError(msg.OUT_OF_STOCK, "out_of_stock", status_code=409, errors={"items": problems})

    lines: list[OrderItem] = []
    subtotal = items_total = 0
    for item in cart_items:
        variant = variants[item.variant_id]
        product = products[variant.product_id]
        final_unit = calc_final_price(product.base_price, product.discount_percent)
        first_image = product.images.order_by("order", "id").first()
        lines.append(
            OrderItem(
                product=product,
                variant=variant,
                title=product.title,
                product_slug=product.slug,
                image=first_image.image.name if first_image else "",
                size=variant.size,
                color=variant.color,
                sku=variant.sku,
                quantity=item.quantity,
                unit_price=product.base_price,
                discount_percent=product.discount_percent,
                final_unit_price=final_unit,
                line_total=final_unit * item.quantity,
            )
        )
        subtotal += product.base_price * item.quantity
        items_total += final_unit * item.quantity

    shipping_cost = method.cost_for(items_total)
    order = Order.objects.create(
        user=user,
        number=next_order_number(),
        status=OrderStatus.PENDING,
        subtotal=subtotal,
        discount_total=subtotal - items_total,
        shipping_cost=shipping_cost,
        total=items_total + shipping_cost,
        shipping_method=method,
        shipping_title=method.title,
        address=address.as_snapshot(),
        note=note,
        expires_at=timezone.now() + timedelta(minutes=settings.ORDER_PAYMENT_TIMEOUT_MINUTES),
    )
    for line in lines:
        line.order = order
    OrderItem.objects.bulk_create(lines)

    for item in cart_items:  # reserve stock
        Variant.objects.filter(pk=item.variant_id).update(stock=F("stock") - item.quantity)

    cart.items.all().delete()
    return order


def release_stock(order: Order) -> None:
    """Give reserved stock back (idempotent). Call inside a transaction with the order locked."""
    if order.stock_released:
        return
    for item in order.items.all():
        if item.variant_id:
            Variant.objects.filter(pk=item.variant_id).update(stock=F("stock") + item.quantity)
    order.stock_released = True
    order.save(update_fields=["stock_released", "updated_at"])


def try_reserve_stock_again(order: Order) -> bool:
    """Used when a payment succeeds after the order was auto-cancelled."""
    items = list(order.items.all())
    variant_ids = sorted({i.variant_id for i in items if i.variant_id})
    variants = {v.id: v for v in Variant.objects.select_for_update().filter(id__in=variant_ids).order_by("id")}
    for item in items:
        variant = variants.get(item.variant_id)
        if variant is None or variant.stock < item.quantity:
            return False
    for item in items:
        Variant.objects.filter(pk=item.variant_id).update(stock=F("stock") - item.quantity)
    order.stock_released = False
    return True


@transaction.atomic
def cancel_order(order_id: int, *, release: bool = True) -> Order:
    order = Order.objects.select_for_update().get(pk=order_id)
    if order.status in (OrderStatus.PENDING, OrderStatus.PAID, OrderStatus.PROCESSING):
        order.status = OrderStatus.CANCELLED
        order.save(update_fields=["status", "updated_at"])
        if release:
            release_stock(order)
        notify_order(order)
    return order


def mark_order_paid(order: Order) -> bool:
    """Mark a locked order as paid. Returns False if it could not be fulfilled (needs refund)."""
    if order.status == OrderStatus.PAID:
        return True
    if order.status == OrderStatus.CANCELLED:
        if not try_reserve_stock_again(order):
            logger.error("Payment received for cancelled order %s but stock is gone", order.number)
            return False
    order.status = OrderStatus.PAID
    order.paid_at = timezone.now()
    order.expires_at = None
    order.save(update_fields=["status", "paid_at", "expires_at", "stock_released", "updated_at"])
    for item in order.items.all():
        if item.product_id:
            Product.objects.filter(pk=item.product_id).update(sales_count=F("sales_count") + item.quantity)
    return True


def cancel_expired_orders() -> int:
    now = timezone.now()
    ids = list(Order.objects.filter(status=OrderStatus.PENDING, expires_at__lt=now).values_list("id", flat=True)[:500])
    cancelled = 0
    for order_id in ids:
        with transaction.atomic():
            order = Order.objects.select_for_update(skip_locked=True).filter(pk=order_id).first()
            if order is None or order.status != OrderStatus.PENDING or not order.expires_at or order.expires_at >= now:
                continue
            # Never cancel an order whose payment is being verified right now.
            if order.payments.filter(status="success").exists():
                continue
            order.status = OrderStatus.CANCELLED
            order.save(update_fields=["status", "updated_at"])
            release_stock(order)
            notify_order(order)
            cancelled += 1
    return cancelled
