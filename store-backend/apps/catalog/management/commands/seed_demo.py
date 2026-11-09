"""Seed realistic Persian demo data: python manage.py seed_demo [--flush]"""

import io
import random

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from PIL import Image, ImageDraw

from apps.catalog.models import Category, Collection, Product, ProductImage, Variant
from apps.content.models import Banner
from apps.orders.models import ShippingMethod
from apps.stores.models import Store

COLORS = [
    ("مشکی", "#1f1f1f"),
    ("سرمه‌ای", "#1e2a4a"),
    ("طوسی", "#8a8d91"),
    ("کرم", "#d8c7a8"),
    ("زیتونی", "#5b6236"),
    ("قهوه‌ای", "#6b4630"),
    ("سفید", "#f2f0eb"),
    ("آبی روشن", "#9cb8d6"),
]
TOP_SIZES = ["S", "M", "L", "XL", "XXL"]
PANT_SIZES = ["30", "32", "34", "36", "38"]

CATALOG = {
    "jackets": (
        "کاپشن و جلیقه",
        [
            ("کاپشن پافر کلاه‌دار", 4_890_000),
            ("جلیقه پفی سبک", 2_350_000),
            ("کت پشمی کلاسیک", 6_200_000),
            ("کاپشن چرم مصنوعی", 5_450_000),
            ("بارانی بلند", 5_900_000),
            ("کاپشن جین", 3_150_000),
            ("جلیقه کتان", 1_890_000),
            ("کت تک اسپرت", 4_700_000),
        ],
        TOP_SIZES,
    ),
    "pants": (
        "شلوار",
        [
            ("شلوار جین اسلیم", 1_950_000),
            ("شلوار کتان راسته", 1_690_000),
            ("شلوار پارچه‌ای رسمی", 2_250_000),
            ("شلوار کارگو", 2_050_000),
            ("شلوار اسلش", 1_350_000),
            ("شلوار جین مام‌فیت", 2_100_000),
            ("شلوارک کتان", 990_000),
            ("شلوار مخمل کبریتی", 2_390_000),
        ],
        PANT_SIZES,
    ),
    "shirts": (
        "پیراهن",
        [
            ("پیراهن آکسفورد", 1_490_000),
            ("پیراهن کتان آستین کوتاه", 1_190_000),
            ("پیراهن چهارخانه فلانل", 1_650_000),
            ("پیراهن رسمی یقه کلاسیک", 1_790_000),
            ("پیراهن لینن", 1_890_000),
            ("پیراهن جین", 1_550_000),
            ("پیراهن یقه دیپلمات", 1_590_000),
            ("پیراهن راه‌راه", 1_420_000),
        ],
        TOP_SIZES,
    ),
}


def make_image(hex_color: str, size: tuple[int, int] = (800, 1000), label_shape: bool = True) -> ContentFile:
    """Simple placeholder: soft background + a garment-like silhouette in the product color."""
    image = Image.new("RGB", size, "#f3f1ed")
    draw = ImageDraw.Draw(image)
    w, h = size
    if label_shape:
        draw.rounded_rectangle([w * 0.28, h * 0.18, w * 0.72, h * 0.85], radius=40, fill=hex_color)
        draw.polygon(
            [(w * 0.28, h * 0.2), (w * 0.12, h * 0.45), (w * 0.2, h * 0.5), (w * 0.3, h * 0.35)], fill=hex_color
        )
        draw.polygon(
            [(w * 0.72, h * 0.2), (w * 0.88, h * 0.45), (w * 0.8, h * 0.5), (w * 0.7, h * 0.35)], fill=hex_color
        )
        draw.ellipse([w * 0.43, h * 0.15, w * 0.57, h * 0.24], fill="#f3f1ed")
    else:
        draw.rectangle([0, 0, w, h], fill=hex_color)
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=82)
    return ContentFile(buffer.getvalue())


class Command(BaseCommand):
    help = "Create demo categories, collections, products, banners, stores and shipping methods."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--flush", action="store_true", help="Delete existing catalog/demo data first")
        parser.add_argument("--seed", type=int, default=42)

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        random.seed(options["seed"])
        if options["flush"]:
            ProductImage.objects.all().delete()
            Variant.objects.all().delete()
            Product.objects.all().delete()
            Collection.objects.all().delete()
            Category.objects.all().delete()
            Banner.objects.all().delete()
            Store.objects.all().delete()
            ShippingMethod.objects.filter(orders__isnull=True).delete()

        if Product.objects.exists():
            self.stdout.write(self.style.WARNING("Products already exist. Use --flush to recreate."))
            return

        spring = Collection.objects.create(
            title="کالکشن بهاره",
            slug="spring-collection",
            description="رنگ‌های روشن و پارچه‌های سبک برای روزهای بهاری",
            is_featured=True,
            order=1,
        )
        spring.banner.save("spring.jpg", make_image("#9cb8d6", (1600, 600), False), save=True)
        winter = Collection.objects.create(
            title="کالکشن زمستانه",
            slug="winter-collection",
            description="گرم و شیک برای روزهای سرد",
            order=2,
        )
        winter.banner.save("winter.jpg", make_image("#1e2a4a", (1600, 600), False), save=True)

        sku_counter = 1000
        for cat_order, (slug, (name, items, sizes)) in enumerate(CATALOG.items()):
            category = Category.objects.create(name=name, slug=slug, order=cat_order)
            category.image.save(f"{slug}.jpg", make_image(COLORS[cat_order][1], (600, 600)), save=True)
            for index, (title, price) in enumerate(items):
                discount = random.choice([0, 0, 0, 10, 15, 20, 25, 30])
                product = Product.objects.create(
                    title=title,
                    slug=f"{slug}-{index + 1}",
                    description=(
                        f"{title} با دوخت باکیفیت و پارچه مرغوب. مناسب استفاده روزمره و مجلسی.\n"
                        "جنس: ترکیب پنبه و پلی‌استر | شستشو: با آب سرد | ساخت ایران"
                    ),
                    category=category,
                    base_price=price,
                    discount_percent=discount,
                )
                product.collections.add(spring if index % 2 == 0 else winter)
                colors = random.sample(COLORS, k=random.choice([2, 3]))
                for color_index, (color_name, hex_code) in enumerate(colors[:2]):
                    img = ProductImage(product=product, alt=f"{title} {color_name}", order=color_index)
                    img.image.save(f"{product.slug}-{color_index}.jpg", make_image(hex_code), save=True)
                for color_name, hex_code in colors:
                    for size in sizes:
                        sku_counter += 1
                        Variant.objects.create(
                            product=product,
                            size=size,
                            color=color_name,
                            color_hex=hex_code,
                            stock=random.choice([0, 2, 5, 8, 12, 20]),
                            sku=f"SKU-{sku_counter}",
                        )

        for order, (title, subtitle, color, link) in enumerate(
            [
                ("کالکشن بهاره رسید", "تا ۳۰٪ تخفیف روی محصولات منتخب", "#9cb8d6", "/collection/spring-collection"),
                ("کاپشن‌های زمستانه", "گرم، سبک و شیک", "#1e2a4a", "/category/jackets"),
                ("حراج پیراهن", "فقط تا پایان هفته", "#d8c7a8", "/category/shirts?on_sale=true"),
            ]
        ):
            banner = Banner(title=title, subtitle=subtitle, link=link, order=order)
            banner.image.save(f"banner-{order}.jpg", make_image(color, (1600, 700), False), save=False)
            banner.image_mobile.save(f"banner-{order}-m.jpg", make_image(color, (800, 1000), False), save=False)
            banner.save()

        Store.objects.bulk_create(
            [
                Store(
                    name="شعبه مرکزی",
                    city="تهران",
                    address="تهران، خیابان ولیعصر، بالاتر از پارک ملت، مجتمع تجاری نگین، طبقه اول",
                    phone="021-22000000",
                    hours="شنبه تا پنجشنبه ۱۰ تا ۲۲",
                    latitude=35.7766,
                    longitude=51.4142,
                    order=1,
                ),
                Store(
                    name="شعبه شمال تهران",
                    city="تهران",
                    address="تهران، تجریش، مرکز خرید ارگ، طبقه دوم",
                    phone="021-22700000",
                    hours="همه‌روزه ۱۰ تا ۲۳",
                    latitude=35.8044,
                    longitude=51.4269,
                    order=2,
                ),
                Store(
                    name="شعبه اصفهان",
                    city="اصفهان",
                    address="اصفهان، خیابان چهارباغ بالا، مجتمع پارک",
                    phone="031-36000000",
                    hours="شنبه تا پنجشنبه ۱۰ تا ۲۲",
                    latitude=32.6366,
                    longitude=51.6608,
                    order=3,
                ),
                Store(
                    name="شعبه شیراز",
                    city="شیراز",
                    address="شیراز، بلوار چمران، مجتمع خلیج فارس",
                    phone="071-36200000",
                    hours="شنبه تا پنجشنبه ۱۰ تا ۲۲",
                    latitude=29.6402,
                    longitude=52.4855,
                    order=4,
                ),
            ]
        )

        if not ShippingMethod.objects.exists():
            ShippingMethod.objects.bulk_create(
                [
                    ShippingMethod(
                        title="پست پیشتاز", description="۳ تا ۵ روز کاری", cost=60_000, free_over=3_000_000, order=1
                    ),
                    ShippingMethod(
                        title="تیپاکس", description="۱ تا ۳ روز کاری", cost=95_000, free_over=5_000_000, order=2
                    ),
                    ShippingMethod(title="پیک (فقط تهران)", description="همان روز / روز بعد", cost=120_000, order=3),
                ]
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Done: {Category.objects.count()} categories, {Product.objects.count()} products, "
                f"{Variant.objects.count()} variants, {Store.objects.count()} stores."
            )
        )
