from django.db.models import QuerySet
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services
from .models import Order, OrderStatus, ShippingMethod
from .serializers import OrderCreateSerializer, OrderSerializer, ShippingMethodSerializer


@extend_schema(tags=["orders"])
class ShippingMethodListView(generics.ListAPIView):
    serializer_class = ShippingMethodSerializer
    pagination_class = None
    queryset = ShippingMethod.objects.filter(is_active=True)


class OrderCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(tags=["orders"], request=OrderCreateSerializer, responses={201: OrderSerializer})
    def post(self, request):
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = services.create_order(request.user, **serializer.validated_data)
        order = Order.objects.select_related("shipping_method").prefetch_related("items").get(pk=order.pk)
        return Response(OrderSerializer(order, context={"request": request}).data, status=status.HTTP_201_CREATED)


def my_orders(user) -> QuerySet[Order]:
    return Order.objects.filter(user=user).select_related("shipping_method").prefetch_related("items")


@extend_schema(
    tags=["me"],
    parameters=[OpenApiParameter("status", OpenApiTypes.STR, enum=[c for c, _ in OrderStatus.choices])],
)
class MyOrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Order.objects.none()
        qs = my_orders(self.request.user)
        status_filter = self.request.query_params.get("status")
        if status_filter in OrderStatus.values:
            qs = qs.filter(status=status_filter)
        return qs


@extend_schema(tags=["me"])
class MyOrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Order.objects.none()
        return my_orders(self.request.user)
