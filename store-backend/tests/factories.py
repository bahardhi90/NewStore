import factory
from django.core.files.base import ContentFile

from apps.accounts.models import Address, User
from apps.catalog.models import Category, Collection, Product, ProductImage, Variant
from apps.orders.models import ShippingMethod
from apps.stores.models import Store

# 1x1 transparent GIF
TINY_GIF = (
    b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,"
    b"\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
)


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ("phone",)

    phone = factory.Sequence(lambda n: f"0912{n:07d}")
    first_name = "علی"
    last_name = "رضایی"


class AddressFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Address

    user = factory.SubFactory(UserFactory)
    title = "خانه"
    receiver_name = "علی رضایی"
    receiver_phone = "09121234567"
    province = "تهران"
    city = "تهران"
    postal_code = "1234567890"
    address_line = "خیابان ولیعصر، پلاک ۱"
    is_default = True


class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Category

    name = factory.Sequence(lambda n: f"دسته {n}")
    slug = factory.Sequence(lambda n: f"cat-{n}")


class CollectionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Collection

    title = factory.Sequence(lambda n: f"کالکشن {n}")
    slug = factory.Sequence(lambda n: f"col-{n}")
    banner = factory.LazyFunction(lambda: ContentFile(TINY_GIF, name="banner.gif"))


class ProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Product

    title = factory.Sequence(lambda n: f"محصول {n}")
    slug = factory.Sequence(lambda n: f"product-{n}")
    category = factory.SubFactory(CategoryFactory)
    base_price = 1_000_000
    discount_percent = 0


class ProductImageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProductImage

    product = factory.SubFactory(ProductFactory)
    image = factory.LazyFunction(lambda: ContentFile(TINY_GIF, name="p.gif"))
    order = factory.Sequence(lambda n: n)


class VariantFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Variant

    product = factory.SubFactory(ProductFactory)
    size = "L"
    color = "مشکی"
    color_hex = "#000000"
    stock = 5
    sku = factory.Sequence(lambda n: f"SKU-T-{n}")


class ShippingMethodFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ShippingMethod

    title = "پست پیشتاز"
    cost = 60_000
    free_over = None


class StoreFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Store

    name = "شعبه مرکزی"
    city = "تهران"
    address = "خیابان ولیعصر"
