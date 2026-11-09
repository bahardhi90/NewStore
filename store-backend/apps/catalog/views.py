from django.conf import settings
from django.core.cache import cache
from django.db.models import Max, Min, Prefetch, QuerySet
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .cache import CATEGORIES_KEY
from .filters import ProductBaseFilter, ProductFilter, sort_sizes
from .models import Category, Collection, Product, ProductImage, Variant
from .serializers import (
    CategorySerializer,
    CollectionSerializer,
    ProductDetailSerializer,
    ProductFilterOptionsSerializer,
    ProductListSerializer,
)

ORDERING_MAP = {
    "newest": ["-created_at", "-id"],
    "price": ["final_price", "-id"],
    "-price": ["-final_price", "-id"],
    "-discount_percent": ["-discount_percent", "-created_at"],
    "popular": ["-sales_count", "-created_at"],
}


def product_list_queryset() -> QuerySet[Product]:
    return Product.objects.filter(is_active=True).prefetch_related(
        Prefetch("images", queryset=ProductImage.objects.order_by("order", "id"))
    )


@extend_schema(tags=["catalog"])
class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CategorySerializer
    pagination_class = None
    queryset = Category.objects.filter(is_active=True)
    http_method_names = ["get", "head", "options"]

    def list(self, request, *args, **kwargs):
        data = cache.get(CATEGORIES_KEY)
        if data is None:
            data = self.get_serializer(self.get_queryset(), many=True).data
            cache.set(CATEGORIES_KEY, data, settings.HOME_CACHE_SECONDS)
        return Response(data)


@extend_schema(tags=["catalog"])
class CollectionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CollectionSerializer
    pagination_class = None
    lookup_field = "slug"
    lookup_value_regex = r"[^/]+"
    queryset = Collection.objects.filter(is_active=True)


@extend_schema_view(
    list=extend_schema(
        tags=["catalog"],
        parameters=[
            OpenApiParameter("search", OpenApiTypes.STR, description="جستجو در عنوان و توضیحات"),
            OpenApiParameter(
                "ordering",
                OpenApiTypes.STR,
                enum=list(ORDERING_MAP.keys()),
                description="پیش‌فرض newest",
            ),
        ],
    ),
    retrieve=extend_schema(tags=["catalog"]),
)
class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_field = "slug"
    lookup_value_regex = r"[^/]+"
    filterset_class = ProductFilter
    filter_backends = [*viewsets.ReadOnlyModelViewSet.filter_backends, filters.SearchFilter]
    search_fields = ["title", "description"]

    def get_queryset(self) -> QuerySet[Product]:
        if self.action == "retrieve":
            return (
                Product.objects.filter(is_active=True)
                .select_related("category")
                .prefetch_related(
                    Prefetch("images", queryset=ProductImage.objects.order_by("order", "id")),
                    Prefetch("variants", queryset=Variant.objects.order_by("id")),
                    Prefetch("collections", queryset=Collection.objects.filter(is_active=True)),
                )
            )
        ordering = ORDERING_MAP.get(self.request.query_params.get("ordering", "newest"), ORDERING_MAP["newest"])
        return product_list_queryset().order_by(*ordering)

    def get_serializer_class(self):
        return ProductDetailSerializer if self.action == "retrieve" else ProductListSerializer

    @extend_schema(
        tags=["catalog"],
        parameters=[
            OpenApiParameter("category", OpenApiTypes.STR),
            OpenApiParameter("collection", OpenApiTypes.STR),
            OpenApiParameter("on_sale", OpenApiTypes.BOOL),
            OpenApiParameter("search", OpenApiTypes.STR),
        ],
        responses=ProductFilterOptionsSerializer,
    )
    @action(detail=False, methods=["get"], url_path="filters", filterset_class=None, pagination_class=None)
    def filter_options(self, request):
        base = Product.objects.filter(is_active=True)
        base = ProductBaseFilter(request.query_params, queryset=base).qs
        search = request.query_params.get("search")
        if search:
            base = filters.SearchFilter().filter_queryset(request, base, self)
        product_ids = base.values("id")
        variants = Variant.objects.filter(product_id__in=product_ids, stock__gt=0)
        # order_by() clears Variant's default ordering; otherwise DISTINCT also compares "id" and repeats sizes
        sizes = sort_sizes(list(variants.values_list("size", flat=True).order_by().distinct()))
        colors_seen: dict[str, str | None] = {}
        for name, hex_code in variants.values_list("color", "color_hex").order_by("color"):
            colors_seen.setdefault(name, hex_code or None)
        prices = Product.objects.filter(id__in=product_ids).aggregate(min=Min("final_price"), max=Max("final_price"))
        data = {
            "sizes": sizes,
            "colors": [{"name": n, "hex": h} for n, h in colors_seen.items()],
            "min_price": prices["min"],
            "max_price": prices["max"],
        }
        return Response(data)
