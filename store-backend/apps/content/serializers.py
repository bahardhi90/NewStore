from rest_framework import serializers

from apps.catalog.serializers import CategorySerializer, CollectionSerializer, ProductListSerializer

from .models import Banner, FooterColumn, FooterLink, Page, PageItem, SiteSettings, SizeChart, TrustBadge


class SizeChartSerializer(serializers.ModelSerializer):
    columns = serializers.ListField(child=serializers.CharField(), source="column_list", read_only=True)
    rows = serializers.ListField(
        child=serializers.ListField(child=serializers.CharField()), source="row_list", read_only=True
    )

    class Meta:
        model = SizeChart
        fields = ["title", "columns", "rows"]


class PageItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PageItem
        fields = ["heading", "body"]


class PageSerializer(serializers.ModelSerializer):
    paragraphs = serializers.ListField(child=serializers.CharField(), read_only=True)
    items = PageItemSerializer(many=True)

    class Meta:
        model = Page
        fields = ["slug", "title", "paragraphs", "items"]


class TrustBadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrustBadge
        fields = ["icon", "title", "subtitle"]


class FooterLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = FooterLink
        fields = ["title", "url"]


class FooterColumnSerializer(serializers.ModelSerializer):
    links = FooterLinkSerializer(many=True)

    class Meta:
        model = FooterColumn
        fields = ["title", "links"]


class SiteSettingsSerializer(serializers.ModelSerializer):
    trust_badges = TrustBadgeSerializer(many=True, source="active_trust_badges")
    footer_columns = FooterColumnSerializer(many=True)
    shipping_points = serializers.ListField(child=serializers.CharField(), read_only=True)
    size_charts = SizeChartSerializer(many=True)

    class Meta:
        model = SiteSettings
        fields = [
            "brand_name",
            "tagline",
            "logo",
            "announcement_text",
            "instagram_url",
            "telegram_url",
            "trust_badges",
            "footer_columns",
            "shipping_points",
            "size_guide_note",
            "size_charts",
        ]


class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        fields = ["id", "title", "subtitle", "image", "image_mobile", "video", "link"]


class CollectionHighlightSerializer(serializers.Serializer):
    collection = CollectionSerializer()
    products = ProductListSerializer(many=True)


class HomeSerializer(serializers.Serializer):
    banners = BannerSerializer(many=True)
    categories = CategorySerializer(many=True)
    on_sale = ProductListSerializer(many=True)
    collection_highlight = CollectionHighlightSerializer(allow_null=True)
    newest = ProductListSerializer(many=True)
