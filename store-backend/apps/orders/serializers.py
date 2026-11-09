from django.core.files.storage import default_storage
from rest_framework import serializers

from apps.accounts.serializers import AddressSerializer

from .models import Order, OrderItem, OrderStatus, ShippingMethod


class ShippingMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingMethod
        fields = ["id", "title", "description", "cost", "free_over"]


class OrderItemSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product_slug",
            "title",
            "image",
            "size",
            "color",
            "quantity",
            "unit_price",
            "discount_percent",
            "final_unit_price",
            "line_total",
        ]

    def get_image(self, obj: OrderItem) -> str | None:
        if not obj.image:
            return None
        url = default_storage.url(obj.image)
        request = self.context.get("request")
        return request.build_absolute_uri(url) if request and url.startswith("/") else url


class OrderAddressSerializer(AddressSerializer):
    class Meta(AddressSerializer.Meta):
        fields = [f for f in AddressSerializer.Meta.fields if f != "id"]


class OrderSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)
    shipping_method = serializers.SerializerMethodField()
    address = serializers.JSONField()

    class Meta:
        model = Order
        fields = [
            "id",
            "number",
            "status",
            "status_display",
            "items",
            "subtotal",
            "discount_total",
            "shipping_cost",
            "total",
            "shipping_method",
            "address",
            "note",
            "tracking_code",
            "expires_at",
            "created_at",
            "paid_at",
        ]

    def get_shipping_method(self, obj: Order) -> dict | None:
        method = obj.shipping_method
        if method is None:
            return None
        return {
            "id": method.id,
            "title": obj.shipping_title or method.title,
            "description": method.description,
            "cost": obj.shipping_cost,
            "free_over": method.free_over,
        }


class OrderCreateSerializer(serializers.Serializer):
    address_id = serializers.IntegerField(min_value=1)
    shipping_method_id = serializers.IntegerField(min_value=1)
    note = serializers.CharField(max_length=500, required=False, allow_blank=True, default="")


class OrderListQuerySerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=OrderStatus.choices, required=False)
