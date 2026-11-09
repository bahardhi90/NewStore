from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import TimeStampedModel

from .events import SPECS, SmsEvent, placeholders, to_pattern_text

MELIPAYAMAK_URL = "https://api.payamak-panel.com/post/send.asmx"


class SmsProvider(models.TextChoices):
    CONSOLE = "console", "آزمایشی (پیامک ارسال نمی‌شود، فقط در لاگ سرور ثبت می‌شود)"
    MELIPAYAMAK = "melipayamak", "ملی پیامک (خط خدماتی / پترن)"


class SmsSettings(TimeStampedModel):
    """Single row: which SMS service is used and its login details."""

    provider = models.CharField("سرویس پیامک", max_length=20, choices=SmsProvider.choices, default=SmsProvider.CONSOLE)
    username = models.CharField("نام کاربری ملی پیامک", max_length=100, blank=True)
    password = models.CharField(
        "رمز عبور / کلید API ملی پیامک",
        max_length=200,
        blank=True,
        help_text="اگر ملی پیامک خطای «باید از ApiKey استفاده کنید» داد، کلید API پنل را اینجا وارد کنید.",
    )
    api_url = models.URLField("آدرس وب‌سرویس", default=MELIPAYAMAK_URL, help_text="معمولاً نیازی به تغییر ندارد.")

    class Meta:
        verbose_name = "تنظیمات پیامک"
        verbose_name_plural = "تنظیمات پیامک"

    def __str__(self) -> str:
        return "تنظیمات پیامک"

    @classmethod
    def load(cls) -> "SmsSettings":
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def clean(self) -> None:
        if self.provider != SmsProvider.MELIPAYAMAK:
            return
        missing = [label for label, value in (("نام کاربری", self.username), ("رمز عبور", self.password)) if not value]
        if missing:
            raise ValidationError(f"برای فعال کردن ملی پیامک این موارد را وارد کنید: {'، '.join(missing)}")
        without_pattern = SmsTemplate.objects.filter(is_active=True, body_id__isnull=True)
        if without_pattern.exists():
            names = "، ".join(t.get_event_display() for t in without_pattern)
            raise ValidationError(
                f"این پیامک‌ها فعال هستند ولی کد پترن ندارند: {names}. "
                "ابتدا در بخش «پیامک‌های خودکار» کد پترن آن‌ها را وارد یا غیرفعالشان کنید."
            )


class SmsTemplate(TimeStampedModel):
    """One automatic message per event; the text must match the pattern approved in Melipayamak."""

    event = models.CharField("رویداد", max_length=30, choices=SmsEvent.choices, unique=True)
    is_active = models.BooleanField("فعال", default=False)
    text = models.TextField(
        "متن پیامک",
        help_text="متغیرها را داخل آکولاد بنویسید، مثلاً {name} یا {order_number}. فهرست متغیرهای مجاز پایین‌تر آمده است.",
    )
    body_id = models.PositiveIntegerField(
        "کد پترن (bodyId)",
        null=True,
        blank=True,
        help_text="کدی که ملی پیامک پس از تأیید متن به شما می‌دهد.",
    )

    class Meta:
        verbose_name = "پیامک خودکار"
        verbose_name_plural = "پیامک‌های خودکار"
        ordering = ["id"]

    def __str__(self) -> str:
        return self.get_event_display()

    @property
    def spec(self):
        return SPECS[self.event]

    @property
    def pattern_text(self) -> str:
        return to_pattern_text(self.text)

    def clean(self) -> None:
        if self.event not in SPECS:
            return
        allowed = self.spec.variables
        unknown = [name for name in placeholders(self.text) if name not in allowed]
        if unknown:
            raise ValidationError(
                {
                    "text": f"متغیر ناشناخته: {'، '.join('{' + n + '}' for n in unknown)}. متغیرهای مجاز: "
                    + "، ".join("{" + n + "}" for n in allowed)
                }
            )
        if self.event == SmsEvent.OTP:
            if "code" not in placeholders(self.text):
                raise ValidationError({"text": "متن پیامک ورود باید شامل {code} باشد."})
            if not self.is_active:
                raise ValidationError(
                    {"is_active": "پیامک کد ورود را نمی‌توان غیرفعال کرد؛ بدون آن کسی وارد سایت نمی‌شود."}
                )
        if self.is_active and self.body_id is None and SmsSettings.load().provider == SmsProvider.MELIPAYAMAK:
            raise ValidationError({"body_id": "برای فعال بودن این پیامک، کد پترن را وارد کنید."})


class SmsLog(models.Model):
    class Status(models.TextChoices):
        SENT = "sent", "ارسال شد"
        FAILED = "failed", "ناموفق"

    created_at = models.DateTimeField("زمان", auto_now_add=True, db_index=True)
    event = models.CharField("رویداد", max_length=30, choices=SmsEvent.choices)
    phone = models.CharField("شماره", max_length=15, db_index=True)
    text = models.TextField("متن")
    provider = models.CharField("سرویس", max_length=20, choices=SmsProvider.choices)
    status = models.CharField("وضعیت", max_length=10, choices=Status.choices)
    detail = models.CharField("پاسخ سرویس / خطا", max_length=300, blank=True)

    class Meta:
        verbose_name = "گزارش پیامک"
        verbose_name_plural = "گزارش پیامک‌ها"
        ordering = ["-created_at", "-id"]

    def __str__(self) -> str:
        return f"{self.get_event_display()} → {self.phone}"
