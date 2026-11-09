from rest_framework import serializers

from .models import Category, Collection, Product, ProductImage, Variant


def absolute_url(request, file_field) -> str | None:
    if not file_field:
        return None
    url = file_field.url
    return request.build_absolute_uri(url) if request is not None and url.startswith("/") else url


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "parent", "image"]


class CollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection
        fields = ["id", "title", "slug", "description", "banner", "banner_mobile"]


class VariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Variant
        fields = ["id", "size", "color", "color_hex", "stock"]


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["image", "alt", "color"]


class ProductListSerializer(serializers.ModelSerializer):
    """Expects `images` to be prefetched (ordered)."""

    image = serializers.SerializerMethodField()
    hover_image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ["id", "title", "slug", "image", "hover_image", "base_price", "discount_percent", "final_price"]

    def _image_at(self, obj: Product, index: int) -> str | None:
        images = list(obj.images.all())
        if len(images) > index:
            return absolute_url(self.context.get("request"), images[index].image)
        return None

    def get_image(self, obj: Product) -> str | None:
        return self._image_at(obj, 0)

    def get_hover_image(self, obj: Product) -> str | None:
        return self._image_at(obj, 1)


class ProductDetailSerializer(ProductListSerializer):
    category = CategorySerializer()
    collections = CollectionSerializer(many=True)
    images = ProductImageSerializer(many=True)
    variants = VariantSerializer(many=True)

    class Meta(ProductListSerializer.Meta):
        fields = ProductListSerializer.Meta.fields + ["description", "category", "collections", "images", "variants"]


class ColorOptionSerializer(serializers.Serializer):
    name = serializers.CharField()
    hex = serializers.CharField(allow_null=True)


class ProductFilterOptionsSerializer(serializers.Serializer):
    sizes = serializers.ListField(child=serializers.CharField())
    colors = ColorOptionSerializer(many=True)
    min_price = serializers.IntegerField(allow_null=True)
    max_price = serializers.IntegerField(allow_null=True)
