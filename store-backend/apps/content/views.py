from django.conf import settings
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.catalog.cache import HOME_KEY
from apps.catalog.models import Category, Collection
from apps.catalog.serializers import CategorySerializer, CollectionSerializer, ProductListSerializer
from apps.catalog.views import product_list_queryset

from .models import Banner, Page, SiteSettings
from .serializers import BannerSerializer, HomeSerializer, PageSerializer, SiteSettingsSerializer

HOME_PRODUCTS = 8


class SiteSettingsView(APIView):
    @extend_schema(tags=["home"], responses=SiteSettingsSerializer)
    def get(self, request):
        site = SiteSettings.load()
        site = SiteSettings.objects.prefetch_related("footer_columns__links", "size_charts").get(pk=site.pk)
        return Response(SiteSettingsSerializer(site, context={"request": request}).data)


class PageView(APIView):
    @extend_schema(tags=["home"], responses=PageSerializer)
    def get(self, request, slug: str):
        page = get_object_or_404(Page.objects.prefetch_related("items"), slug=slug)
        return Response(PageSerializer(page).data)


class HomeView(APIView):
    """Everything the home page needs in one cached request."""

    @extend_schema(tags=["home"], responses=HomeSerializer)
    def get(self, request):
        data = cache.get(HOME_KEY)
        if data is None:
            data = self._build(request)
            cache.set(HOME_KEY, data, settings.HOME_CACHE_SECONDS)
        return Response(data)

    def _build(self, request) -> dict:
        ctx = {"request": request}
        products = product_list_queryset()
        collection = Collection.objects.filter(is_active=True).order_by("-is_featured", "order", "-created_at").first()
        highlight = None
        if collection is not None:
            highlight = {
                "collection": CollectionSerializer(collection, context=ctx).data,
                "products": ProductListSerializer(
                    products.filter(collections=collection).order_by("-created_at")[:HOME_PRODUCTS],
                    many=True,
                    context=ctx,
                ).data,
            }
        return {
            "banners": BannerSerializer(Banner.objects.filter(is_active=True), many=True, context=ctx).data,
            "categories": CategorySerializer(
                Category.objects.filter(is_active=True, parent__isnull=True), many=True, context=ctx
            ).data,
            "on_sale": ProductListSerializer(
                products.filter(discount_percent__gt=0).order_by("-discount_percent", "-created_at")[:HOME_PRODUCTS],
                many=True,
                context=ctx,
            ).data,
            "collection_highlight": highlight,
            "newest": ProductListSerializer(
                products.order_by("-created_at")[:HOME_PRODUCTS], many=True, context=ctx
            ).data,
        }
