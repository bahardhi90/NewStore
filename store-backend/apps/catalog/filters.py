import django_filters
from django.db.models import Exists, OuterRef, QuerySet

from .models import Category, Product, Variant, normalize_size

SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL", "XXXL", "3XL", "4XL"]


def _csv(value: str) -> list[str]:
    return [part.strip() for part in (value or "").split(",") if part.strip()]


def category_with_descendants(slug: str) -> list[int]:
    categories = list(Category.objects.filter(is_active=True).values("id", "slug", "parent_id"))
    root = next((c for c in categories if c["slug"] == slug), None)
    if root is None:
        return []
    ids = {root["id"]}
    changed = True
    while changed:
        changed = False
        for c in categories:
            if c["parent_id"] in ids and c["id"] not in ids:
                ids.add(c["id"])
                changed = True
    return list(ids)


class ProductFilter(django_filters.FilterSet):
    category = django_filters.CharFilter(method="filter_category", label="اسلاگ دسته‌بندی")
    collection = django_filters.CharFilter(field_name="collections__slug", label="اسلاگ کالکشن")
    on_sale = django_filters.BooleanFilter(method="filter_on_sale", label="فقط تخفیف‌دار")
    size = django_filters.CharFilter(method="filter_size", label="سایزها (با کاما)")
    color = django_filters.CharFilter(method="filter_color", label="رنگ‌ها (با کاما)")
    min_price = django_filters.NumberFilter(field_name="final_price", lookup_expr="gte")
    max_price = django_filters.NumberFilter(field_name="final_price", lookup_expr="lte")

    class Meta:
        model = Product
        fields = ["category", "collection", "on_sale", "size", "color", "min_price", "max_price"]

    def filter_category(self, queryset: QuerySet, name: str, value: str) -> QuerySet:
        return queryset.filter(category_id__in=category_with_descendants(value))

    def filter_on_sale(self, queryset: QuerySet, name: str, value: bool) -> QuerySet:
        return queryset.filter(discount_percent__gt=0) if value else queryset

    def filter_size(self, queryset: QuerySet, name: str, value: str) -> QuerySet:
        sizes = [normalize_size(s) for s in _csv(value)]
        if not sizes:
            return queryset
        return queryset.filter(Exists(Variant.objects.filter(product=OuterRef("pk"), size__in=sizes, stock__gt=0)))

    def filter_color(self, queryset: QuerySet, name: str, value: str) -> QuerySet:
        colors = _csv(value)
        if not colors:
            return queryset
        return queryset.filter(Exists(Variant.objects.filter(product=OuterRef("pk"), color__in=colors, stock__gt=0)))


class ProductBaseFilter(ProductFilter):
    """Only the 'scope' filters, used to compute available filter options."""

    class Meta:
        model = Product
        fields = ["category", "collection", "on_sale"]


def sort_sizes(sizes: list[str]) -> list[str]:
    def key(size: str) -> tuple[int, int, str]:
        upper = size.upper()
        if upper in SIZE_ORDER:
            return (0, SIZE_ORDER.index(upper), size)
        if size.isdigit():
            return (1, int(size), size)
        return (2, 0, size)

    return sorted(sizes, key=key)
