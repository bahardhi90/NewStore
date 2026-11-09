from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import TimeStampedModel
from apps.orders.models import Order


class PaymentStatus(models.TextChoices):
    INITIATED = "initiated", "شروع‌شده"
    SUCCESS = "success", "موفق"
    FAILED = "failed", "ناموفق"
    CANCELLED = "cancelled", "لغوشده"


class PaymentCode(models.TextChoices):
    ZARINPAL = "zarinpal", "زرین‌پال"
    DIGIPAY = "digipay", "دیجی‌پی"
    SNAPPPAY = "snapppay", "اسنپ‌پی"
    FAKE = "fake", "درگاه آزمایشی"


REQUIRED_CREDENTIALS = {
    PaymentCode.ZARINPAL: ["merchant_id"],
    PaymentCode.DIGIPAY: ["username", "password", "client_id", "client_secret"],
    PaymentCode.SNAPPPAY: ["username", "password", "client_id", "client_secret"],
    PaymentCode.FAKE: [],
}


def token_cache_key(code: str) -> str:
    return f"payments:token:{code}"


class PaymentMethodQuerySet(models.QuerySet):
    def available(self) -> "PaymentMethodQuerySet":
        """Methods customers can choose. The fake gateway never appears unless .env selects it."""
        methods = self.filter(is_active=True)
        if settings.PAYMENT_GATEWAY != PaymentCode.FAKE:
            methods = methods.exclude(code=PaymentCode.FAKE)
        return methods


class PaymentMethod(TimeStampedModel):
    """Payment options at checkout, managed from Django admin (no .env or deploy needed)."""

    code = models.CharField("درگاه", max_length=30, choices=PaymentCode.choices, unique=True)
    title = models.CharField("عنوان نمایشی", max_length=100)
    description = models.CharField("توضیحات", max_length=200, blank=True)
    logo = models.ImageField("لوگو", upload_to="payment-methods/", null=True, blank=True)
    is_active = models.BooleanField("فعال", default=False)
    order = models.PositiveIntegerField("ترتیب", default=0)
    min_amount = models.PositiveIntegerField("حداقل مبلغ (تومان)", null=True, blank=True)
    max_amount = models.PositiveIntegerField("حداکثر مبلغ (تومان)", null=True, blank=True)

    sandbox = models.BooleanField("حالت آزمایشی (Sandbox)", default=False)
    api_url = models.URLField("آدرس API", blank=True, help_text="فقط اگر درگاه آدرس جداگانه‌ای به شما داده است.")
    merchant_id = models.CharField("شناسه پذیرنده (Merchant ID)", max_length=100, blank=True)
    username = models.CharField("نام کاربری", max_length=150, blank=True)
    password = models.CharField("رمز عبور", max_length=255, blank=True)
    client_id = models.CharField("Client ID", max_length=255, blank=True)
    client_secret = models.CharField("Client Secret", max_length=255, blank=True)
    category = models.CharField(
        "دسته‌بندی کالا نزد درگاه",
        max_length=100,
        blank=True,
        default="پوشاک",
        help_text="مقدار مورد قبول درگاه اقساطی.",
    )

    objects = PaymentMethodQuerySet.as_manager()

    class Meta:
        verbose_name = "روش پرداخت"
        verbose_name_plural = "روش‌های پرداخت"
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return self.title

    def missing_credentials(self) -> list[str]:
        fields = REQUIRED_CREDENTIALS.get(self.code, [])
        missing = [name for name in fields if not getattr(self, name)]
        if self.code == PaymentCode.ZARINPAL and settings.ZARINPAL_MERCHANT_ID:
            missing = []  # older installs keep the merchant id in .env
        return missing

    def clean(self) -> None:
        if self.min_amount is not None and self.max_amount is not None and self.min_amount > self.max_amount:
            raise ValidationError("حداقل مبلغ نباید از حداکثر مبلغ بیشتر باشد.")
        missing = self.missing_credentials()
        if self.is_active and missing:
            # A non-field error, so it also works from the editable checkbox in the list page.
            names = "، ".join(str(self._meta.get_field(name).verbose_name) for name in missing)
            raise ValidationError(f"برای فعال‌سازی «{self.title}» ابتدا این موارد را تکمیل کنید: {names}")

    def save(self, *args, **kwargs) -> None:
        super().save(*args, **kwargs)
        cache.delete(token_cache_key(self.code))  # credentials may have changed

    def supports_amount(self, amount: int) -> bool:
        if self.min_amount is not None and amount < self.min_amount:
            return False
        return self.max_amount is None or amount <= self.max_amount


class Payment(TimeStampedModel):
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="payments", verbose_name="سفارش")
    amount = models.PositiveIntegerField("مبلغ (تومان)")
    gateway = models.CharField("درگاه", max_length=30)
    authority = models.CharField("Authority", max_length=100, unique=True, null=True, blank=True)
    ref_id = models.CharField("کد پیگیری بانک", max_length=100, blank=True)
    card_pan = models.CharField("شماره کارت (ماسک‌شده)", max_length=30, blank=True)
    status = models.CharField(
        "وضعیت", max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.INITIATED, db_index=True
    )
    raw_request = models.JSONField("پاسخ شروع پرداخت", default=dict, blank=True)
    raw_response = models.JSONField("پاسخ تأیید پرداخت", default=dict, blank=True)
    verified_at = models.DateTimeField("زمان تأیید", null=True, blank=True)
    needs_refund = models.BooleanField("نیاز به استرداد", default=False)

    class Meta:
        verbose_name = "پرداخت"
        verbose_name_plural = "پرداخت‌ها"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.order.number} - {self.get_status_display()}"
