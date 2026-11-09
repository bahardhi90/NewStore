from django.conf import settings
from rest_framework import serializers

from apps.catalog.serializers import VariantSerializer, absolute_url

from .services import CartView, cart_totals, item_warning, line_prices


class CartItemProductSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    slug = serializers.CharField()
    image = serializers.CharField(allow_null=True)


class CartItemSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    product = CartItemProductSerializer()
    variant = VariantSerializer()
    quantity = serializers.IntegerField()
    unit_price = serializers.IntegerField()
    discount_percent = serializers.IntegerField()
    final_unit_price = serializers.IntegerField()
    line_total = serializers.IntegerField()
    warning = serializers.CharField(allow_null=True)


class CartSerializer(serializers.Serializer):
    """Read-only representation built from a CartView."""

    id = serializers.IntegerField()
    items = CartItemSerializer(many=True)
    item_count = serializers.IntegerField()
    subtotal = serializers.IntegerField()
    discount_total = serializers.IntegerField()
    total = serializers.IntegerField()
    warnings = serializers.ListField(child=serializers.CharField())

    @staticmethod
    def build(view: CartView, request) -> dict:
        items = []
        for item in view.items:
            product = item.variant.product
            images = list(product.images.all())
            items.append(
                {
                    "id": item.id,
                    "product": {
                        "id": product.id,
                        "title": product.title,
                        "slug": product.slug,
                        "image": absolute_url(request, images[0].image) if images else None,
                    },
                    "variant": VariantSerializer(item.variant).data,
                    "quantity": item.quantity,
                    **line_prices(item),
                    "warning": item_warning(item),
                }
            )
        return {"id": view.cart.id, "items": items, **cart_totals(view.items), "warnings": view.warnings}


class CartItemCreateSerializer(serializers.Serializer):
    variant_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1, max_value=settings.CART_MAX_QUANTITY)


class CartItemUpdateSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1, max_value=settings.CART_MAX_QUANTITY)


class CartMergeItemSerializer(serializers.Serializer):
    variant_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1, max_value=100)


class CartMergeSerializer(serializers.Serializer):
    items = CartMergeItemSerializer(many=True, max_length=50)
