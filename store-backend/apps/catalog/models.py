from django.core.validators import MaxValueValidator
from django.db import models

from apps.core.models import TimeStampedModel
from apps.core.pricing import calc_final_price


class Category(TimeStampedModel):
    name = models.CharField("نام", max_length=100)
    slug = models.SlugField("اسلاگ", max_length=120, unique=True, allow_unicode=True)
    parent = models.ForeignKey(
        "self", on_delete=models.PROTECT, null=True, blank=True, related_name="children", verbose_name="والد"
    )
    image = models.ImageField("تصویر", upload_to="categories/", null=True, blank=True)
    order = models.PositiveIntegerField("ترتیب", default=0)
    is_active = models.BooleanField("فعال", default=True)

    class Meta:
        verbose_name = "دسته‌بندی"
        verbose_name_plural = "دسته‌بندی‌ها"
        ordering = ["order", "name"]

    def __str__(self) -> str:
        return self.name


class Collection(TimeStampedModel):
    title = models.CharField("عنوان", max_length=100)
    slug = models.SlugField("اسلاگ", max_length=120, unique=True, allow_unicode=True)
    description = models.TextField("توضیحات", blank=True)
    banner = models.ImageField("بنر", upload_to="collections/")
    banner_mobile = models.ImageField("بنر موبایل", upload_to="collections/", null=True, blank=True)
    is_active = models.BooleanField("فعال", default=True)
    is_featured = models.BooleanField("نمایش در صفحه اصلی", default=False)
    order = models.PositiveIntegerField("ترتیب", default=0)

    class Meta:
        verbose_name = "کالکشن"
        verbose_name_plural = "کالکشن‌ها"
        ordering = ["order", "-created_at"]

    def __str__(self) -> str:
        return self.title


class Product(TimeStampedModel):
    title = models.CharField("عنوان", max_length=200)
    slug = models.SlugField("اسلاگ", max_length=220, unique=True, allow_unicode=True)
    description = models.TextField("توضیحات", blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products", verbose_name="دسته‌بندی")
    collections = models.ManyToManyField(Collection, related_name="products", blank=True, verbose_name="کالکشن‌ها")
    base_price = models.PositiveIntegerField("قیمت پایه (تومان)")
    discount_percent = models.PositiveSmallIntegerField("درصد تخفیف", default=0, validators=[MaxValueValidator(90)])
    final_price = models.PositiveIntegerField("قیمت نهایی (تومان)", editable=False, default=0)
    is_active = models.BooleanField("فعال", default=True)
    sales_count = models.PositiveIntegerField("تعداد فروش", default=0, editable=False)

    class Meta:
        verbose_name = "محصول"
        verbose_name_plural = "محصولات"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["is_active", "-created_at"], name="product_active_new_idx"),
            models.Index(fields=["is_active", "final_price"], name="product_active_price_idx"),
            models.Index(fields=["is_active", "discount_percent"], name="product_active_disc_idx"),
            models.Index(fields=["is_active", "-sales_count"], name="product_active_sales_idx"),
        ]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs) -> None:
        self.final_price = calc_final_price(self.base_price, self.discount_percent)
        update_fields = kwargs.get("update_fields")
        if update_fields is not None and ({"base_price", "discount_percent"} & set(update_fields)):
            kwargs["update_fields"] = list(set(update_fields) | {"final_price"})
        super().save(*args, **kwargs)


class Variant(TimeStampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants", verbose_name="محصول")
    size = models.CharField("سایز", max_length=10, db_index=True)
    color = models.CharField("رنگ", max_length=30, db_index=True)
    color_hex = models.CharField("کد رنگ", max_length=7, blank=True)
    stock = models.PositiveIntegerField("موجودی", default=0)
    sku = models.CharField("SKU", max_length=50, unique=True)

    class Meta:
        verbose_name = "تنوع"
        verbose_name_plural = "تنوع‌ها"
        ordering = ["id"]
        constraints = [models.UniqueConstraint(fields=["product", "size", "color"], name="unique_variant_per_product")]

    def __str__(self) -> str:
        return f"{self.product.title} / {self.size} / {self.color}"

    def normalize(self) -> None:
        """Treat ' s' and 'S' as the same size, otherwise the filters list it twice."""
        self.size = normalize_size(self.size)
        self.color = " ".join((self.color or "").split())

    def clean(self) -> None:
        # Runs before the unique (product, size, color) check in admin forms.
        self.normalize()
        super().clean()

    def save(self, *args, **kwargs) -> None:
        self.normalize()
        super().save(*args, **kwargs)


def normalize_size(size: str) -> str:
    return " ".join((size or "").split()).upper()


class ProductImage(TimeStampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images", verbose_name="محصول")
    image = models.ImageField("تصویر", upload_to="products/")
    color = models.CharField(
        "رنگ", max_length=30, blank=True, help_text="با انتخاب این رنگ در صفحه محصول، این تصویر نمایش داده می‌شود."
    )
    alt = models.CharField("متن جایگزین", max_length=200, blank=True)
    order = models.PositiveIntegerField("ترتیب", default=0)

    class Meta:
        verbose_name = "تصویر محصول"
        verbose_name_plural = "تصاویر محصول"
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return f"{self.product.title} #{self.order}"
