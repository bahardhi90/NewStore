from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services
from .serializers import (
    CartItemCreateSerializer,
    CartItemUpdateSerializer,
    CartMergeSerializer,
    CartSerializer,
)


class _CartBase(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def respond(self, view: services.CartView, code: int = status.HTTP_200_OK) -> Response:
        return Response(CartSerializer.build(view, self.request), status=code)


class CartView(_CartBase):
    @extend_schema(tags=["cart"], responses=CartSerializer)
    def get(self, request):
        return self.respond(services.load_cart(request.user))


class CartItemsView(_CartBase):
    @extend_schema(tags=["cart"], request=CartItemCreateSerializer, responses={201: CartSerializer})
    def post(self, request):
        serializer = CartItemCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        view = services.add_item(request.user, **serializer.validated_data)
        return self.respond(view, status.HTTP_201_CREATED)


class CartItemDetailView(_CartBase):
    @extend_schema(tags=["cart"], request=CartItemUpdateSerializer, responses=CartSerializer)
    def patch(self, request, pk: int):
        serializer = CartItemUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return self.respond(services.update_item(request.user, pk, serializer.validated_data["quantity"]))

    @extend_schema(tags=["cart"], responses=CartSerializer)
    def delete(self, request, pk: int):
        return self.respond(services.remove_item(request.user, pk))


class CartMergeView(_CartBase):
    @extend_schema(tags=["cart"], request=CartMergeSerializer, responses=CartSerializer)
    def post(self, request):
        serializer = CartMergeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return self.respond(services.merge_items(request.user, serializer.validated_data["items"]))
