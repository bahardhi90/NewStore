"""Cart business logic. Prices are never taken from the client."""

from dataclasses import dataclass, field

from django.conf import settings
from django.db import transaction
from django.db.models import Prefetch

from apps.catalog.models import ProductImage, Variant
from apps.core import messages as msg
from apps.core.exceptions import StoreError
from apps.core.pricing import calc_final_price
from apps.core.utils import fa_digits

from .models import Cart, CartItem


@dataclass
class CartView:
    cart: Cart
    items: list[CartItem]
    warnings: list[str] = field(default_factory=list)


def _items_queryset(cart: Cart):
    return cart.items.select_related("variant__product").prefetch_related(
        Prefetch("variant__product__images", queryset=ProductImage.objects.order_by("order", "id"))
    )


def get_cart(user) -> Cart:
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


def load_cart(user, warnings: list[str] | None = None) -> CartView:
    cart = get_cart(user)
    return CartView(cart=cart, items=list(_items_queryset(cart)), warnings=warnings or [])


def _get_variant(variant_id: int) -> Variant:
    variant = Variant.objects.select_related("product").filter(pk=variant_id, product__is_active=True).first()
    if variant is None:
        raise StoreError(
            msg.VARIANT_NOT_FOUND, "not_found", status_code=404, errors={"variant_id": [msg.VARIANT_NOT_FOUND]}
        )
    return variant


def _check_quantity(variant: Variant, quantity: int) -> None:
    max_qty = settings.CART_MAX_QUANTITY
    if quantity > max_qty:
        text = msg.MAX_QUANTITY.format(count=fa_digits(max_qty))
        raise StoreError(text, "validation_error", errors={"quantity": [text]})
    if quantity > variant.stock:
        text = msg.SOLD_OUT if variant.stock == 0 else msg.ONLY_N_IN_STOCK.format(count=fa_digits(variant.stock))
        raise StoreError(msg.OUT_OF_STOCK, "out_of_stock", status_code=409, errors={"variant_id": [text]})


@transaction.atomic
def add_item(user, variant_id: int, quantity: int) -> CartView:
    variant = _get_variant(variant_id)
    cart = get_cart(user)
    item = CartItem.objects.select_for_update().filter(cart=cart, variant=variant).first()
    new_quantity = (item.quantity if item else 0) + quantity
    _check_quantity(variant, new_quantity)
    if item:
        item.quantity = new_quantity
        item.save(update_fields=["quantity", "updated_at"])
    else:
        CartItem.objects.create(cart=cart, variant=variant, quantity=quantity)
    return load_cart(user)


@transaction.atomic
def update_item(user, item_id: int, quantity: int) -> CartView:
    cart = get_cart(user)
    item = CartItem.objects.select_for_update().select_related("variant__product").filter(pk=item_id, cart=cart).first()
    if item is None:
        raise StoreError(msg.NOT_FOUND, "not_found", status_code=404)
    _check_quantity(item.variant, quantity)
    item.quantity = quantity
    item.save(update_fields=["quantity", "updated_at"])
    return load_cart(user)


def remove_item(user, item_id: int) -> CartView:
    cart = get_cart(user)
    deleted, _ = CartItem.objects.filter(pk=item_id, cart=cart).delete()
    if not deleted:
        raise StoreError(msg.NOT_FOUND, "not_found", status_code=404)
    return load_cart(user)


@transaction.atomic
def merge_items(user, items: list[dict]) -> CartView:
    """Merge a guest cart. Never fails because of stock: problems become warnings."""
    cart = get_cart(user)
    max_qty = settings.CART_MAX_QUANTITY
    warnings: list[str] = []

    wanted: dict[int, int] = {}
    for entry in items:
        wanted[entry["variant_id"]] = wanted.get(entry["variant_id"], 0) + entry["quantity"]

    variants = Variant.objects.select_related("product").in_bulk(list(wanted.keys()))
    existing = {item.variant_id: item for item in CartItem.objects.select_for_update().filter(cart=cart)}

    for variant_id, qty in wanted.items():
        variant = variants.get(variant_id)
        if variant is None or not variant.product.is_active:
            warnings.append(msg.MERGE_SKIPPED.format(title=f"#{variant_id}", reason=msg.PRODUCT_UNAVAILABLE))
            continue
        current = existing.get(variant_id)
        desired = (current.quantity if current else 0) + qty
        allowed = min(desired, variant.stock, max_qty)
        if allowed <= 0:
            warnings.append(msg.MERGE_SKIPPED.format(title=variant.product.title, reason=msg.SOLD_OUT))
            continue
        if allowed < desired:
            warnings.append(msg.MERGE_REDUCED.format(title=variant.product.title, count=fa_digits(allowed)))
        if current:
            current.quantity = allowed
            current.save(update_fields=["quantity", "updated_at"])
        else:
            CartItem.objects.create(cart=cart, variant=variant, quantity=allowed)

    return load_cart(user, warnings=warnings)


def item_warning(item: CartItem) -> str | None:
    variant = item.variant
    if not variant.product.is_active:
        return msg.PRODUCT_UNAVAILABLE
    if variant.stock == 0:
        return msg.SOLD_OUT
    if item.quantity > variant.stock:
        return msg.ONLY_N_IN_STOCK.format(count=fa_digits(variant.stock))
    return None


def line_prices(item: CartItem) -> dict[str, int]:
    product = item.variant.product
    final_unit = calc_final_price(product.base_price, product.discount_percent)
    return {
        "unit_price": product.base_price,
        "discount_percent": product.discount_percent,
        "final_unit_price": final_unit,
        "line_total": final_unit * item.quantity,
    }


def cart_totals(items: list[CartItem]) -> dict[str, int]:
    subtotal = total = count = 0
    for item in items:
        prices = line_prices(item)
        subtotal += prices["unit_price"] * item.quantity
        total += prices["line_total"]
        count += item.quantity
    return {"item_count": count, "subtotal": subtotal, "discount_total": subtotal - total, "total": total}
