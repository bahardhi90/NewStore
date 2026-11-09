from django.conf import settings
from django.db import models

from apps.catalog.models import Product, Variant
from apps.core import messages as msg
from apps.core.models import TimeStampedModel


class ShippingMethod(TimeStampedModel):
    title = models.CharField("عنوان", max_length=100)
    description = models.CharField("توضیحات", max_length=200, blank=True)
    cost = models.PositiveIntegerField("هزینه (تومان)")
    free_over = models.PositiveIntegerField("رایگان برای خرید بالای (تومان)", null=True, blank=True)
    is_active = models.BooleanField("فعال", default=True)
    order = models.PositiveIntegerField("ترتیب", default=0)

    class Meta:
        verbose_name = "روش ارسال"
        verbose_name_plural = "روش‌های ارسال"
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return self.title

    def cost_for(self, items_total: int) -> int:
        if self.free_over is not None and items_total >= self.free_over:
            return 0
        return self.cost


class OrderStatus(models.TextChoices):
    PENDING = "pending", msg.ORDER_STATUS_LABELS["pending"]
    PAID = "paid", msg.ORDER_STATUS_LABELS["paid"]
    PROCESSING = "processing", msg.ORDER_STATUS_LABELS["processing"]
    SHIPPED = "shipped", msg.ORDER_STATUS_LABELS["shipped"]
    DELIVERED = "delivered", msg.ORDER_STATUS_LABELS["delivered"]
    CANCELLED = "cancelled", msg.ORDER_STATUS_LABELS["cancelled"]
    REFUNDED = "refunded", msg.ORDER_STATUS_LABELS["refunded"]


class OrderNumberSequence(models.Model):
    """Per-Jalali-year counter used to generate human-friendly order numbers."""

    year = models.PositiveIntegerField(primary_key=True)
    last_value = models.PositiveIntegerField(default=0)


class Order(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="orders", verbose_name="کاربر"
    )
    number = models.CharField("شماره سفارش", max_length=20, unique=True)
    status = models.CharField(
        "وضعیت", max_length=20, choices=OrderStatus.choices, default=OrderStatus.PENDING, db_index=True
    )
    subtotal = models.PositiveIntegerField("جمع قیمت پایه")
    discount_total = models.PositiveIntegerField("جمع تخفیف")
    shipping_cost = models.PositiveIntegerField("هزینه ارسال")
    total = models.PositiveIntegerField("مبلغ قابل پرداخت")
    shipping_method = models.ForeignKey(
        ShippingMethod, on_delete=models.PROTECT, null=True, related_name="orders", verbose_name="روش ارسال"
    )
    shipping_title = models.CharField("عنوان روش ارسال", max_length=100, blank=True)
    address = models.JSONField("آدرس (نسخه ثبت‌شده)")
    note = models.CharField("توضیحات مشتری", max_length=500, blank=True)
    tracking_code = models.CharField("کد رهگیری مرسوله", max_length=50, blank=True, null=True)
    expires_at = models.DateTimeField("مهلت پرداخت", null=True, blank=True)
    paid_at = models.DateTimeField("زمان پرداخت", null=True, blank=True)
    stock_released = models.BooleanField("موجودی آزاد شده", default=False)

    class Meta:
        verbose_name = "سفارش"
        verbose_name_plural = "سفارش‌ها"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["user", "-created_at"], name="order_user_created_idx"),
            models.Index(fields=["status", "expires_at"], name="order_status_expires_idx"),
        ]

    def __str__(self) -> str:
        return self.number


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, related_name="+")
    variant = models.ForeignKey(Variant, on_delete=models.SET_NULL, null=True, related_name="+")
    title = models.CharField("عنوان", max_length=200)
    product_slug = models.CharField(max_length=220, blank=True)
    image = models.CharField("تصویر", max_length=500, blank=True)
    size = models.CharField("سایز", max_length=10)
    color = models.CharField("رنگ", max_length=30)
    sku = models.CharField(max_length=50, blank=True)
    quantity = models.PositiveSmallIntegerField("تعداد")
    unit_price = models.PositiveIntegerField("قیمت پایه")
    discount_percent = models.PositiveSmallIntegerField("درصد تخفیف")
    final_unit_price = models.PositiveIntegerField("قیمت واحد نهایی")
    line_total = models.PositiveIntegerField("جمع")

    class Meta:
        verbose_name = "آیتم سفارش"
        verbose_name_plural = "آیتم‌های سفارش"
        ordering = ["id"]

    def __str__(self) -> str:
        return f"{self.title} × {self.quantity}"
