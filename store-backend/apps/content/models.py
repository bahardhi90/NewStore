import re

from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models

from apps.core.models import TimeStampedModel

MAX_VIDEO_MB = 20  # keep in line with client_max_body_size in nginx.conf


def validate_video_size(file) -> None:
    if file.size > MAX_VIDEO_MB * 1024 * 1024:
        raise ValidationError(f"حجم ویدیو باید کمتر از {MAX_VIDEO_MB} مگابایت باشد.")


class SiteSettings(TimeStampedModel):
    """Single row: site name, logo, top bar and footer details, editable from admin."""

    brand_name = models.CharField("نام سایت", max_length=60, default="کرامت")
    tagline = models.CharField("شعار سایت", max_length=150, default="پوشاک مردانه با کیفیت و قیمت منصفانه")
    logo = models.ImageField(
        "لوگو",
        upload_to="site/",
        null=True,
        blank=True,
        help_text="تا زمانی که لوگویی بارگذاری نشود، نام سایت در بالای صفحه نمایش داده می‌شود.",
    )
    announcement_text = models.CharField(
        "متن نوار بالای سایت",
        max_length=200,
        blank=True,
        default="ارسال رایگان برای خریدهای بالای ۳ میلیون تومان",
        help_text="برای پنهان کردن نوار، خالی بگذارید.",
    )
    instagram_url = models.URLField("لینک اینستاگرام", blank=True)
    telegram_url = models.URLField("لینک تلگرام", blank=True)
    product_shipping_text = models.TextField(
        "متن «ارسال و مرجوعی» در صفحه محصول", blank=True, help_text="هر خط یک مورد جداگانه نمایش داده می‌شود."
    )
    size_guide_note = models.CharField("توضیح بالای راهنمای سایز", max_length=300, blank=True)

    class Meta:
        verbose_name = "تنظیمات سایت"
        verbose_name_plural = "تنظیمات سایت"

    def __str__(self) -> str:
        return self.brand_name

    @classmethod
    def load(cls) -> "SiteSettings":
        return cls.objects.get_or_create(pk=1)[0]

    @property
    def active_trust_badges(self):
        return self.trust_badges.filter(is_active=True)

    @property
    def shipping_points(self) -> list[str]:
        return non_empty_lines(self.product_shipping_text)


def non_empty_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


CELL_SEPARATOR = re.compile(r"\s*[,،|]\s*")  # Persian comma, comma or |


def split_cells(line: str) -> list[str]:
    return CELL_SEPARATOR.split(line.strip())


class SizeChart(models.Model):
    """One table in the "size guide" window on product pages."""

    site = models.ForeignKey(SiteSettings, on_delete=models.CASCADE, related_name="size_charts")
    title = models.CharField("عنوان جدول", max_length=100, help_text="مثلاً: کاپشن، کت و پیراهن")
    columns = models.CharField("ستون‌ها", max_length=300, help_text="با ویرگول جدا کنید: سایز، دور سینه، قد")
    rows = models.TextField("ردیف‌ها", help_text="هر خط یک سایز، به ترتیب ستون‌ها و با ویرگول جدا شده: S، ۹۶–۱۰۰، ۷۰")
    order = models.PositiveIntegerField("ترتیب", default=0)

    class Meta:
        verbose_name = "جدول سایز"
        verbose_name_plural = "جدول‌های راهنمای سایز"
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return self.title

    @property
    def column_list(self) -> list[str]:
        return split_cells(self.columns)

    @property
    def row_list(self) -> list[list[str]]:
        return [split_cells(line) for line in non_empty_lines(self.rows)]

    def clean(self) -> None:
        expected = len(self.column_list)
        for number, row in enumerate(self.row_list, start=1):
            if len(row) != expected:
                raise ValidationError(
                    {"rows": f"ردیف {number} ({'، '.join(row)}) باید {expected} مقدار داشته باشد، نه {len(row)}."}
                )


class Page(TimeStampedModel):
    """The About, Contact, FAQ and Returns pages. The pages themselves are fixed; their text is editable."""

    class Slug(models.TextChoices):
        ABOUT = "about", "درباره ما"
        CONTACT = "contact", "تماس با ما"
        FAQ = "faq", "سوالات متداول"
        RETURNS = "returns", "شرایط مرجوعی"

    slug = models.CharField("صفحه", max_length=20, choices=Slug.choices, unique=True)
    title = models.CharField("عنوان صفحه", max_length=150)
    body = models.TextField("متن صفحه", blank=True, help_text="برای پاراگراف جدید، یک خط خالی بگذارید.")

    class Meta:
        verbose_name = "صفحه"
        verbose_name_plural = "صفحات"
        ordering = ["id"]

    def __str__(self) -> str:
        return self.get_slug_display()

    @property
    def paragraphs(self) -> list[str]:
        return [p.strip() for p in re.split(r"\n\s*\n", self.body) if p.strip()]


class PageItem(models.Model):
    """FAQ: question/answer. Returns: heading/text. Contact: label/value (phone and email become links)."""

    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name="items")
    heading = models.CharField("عنوان", max_length=200)
    body = models.TextField("متن")
    order = models.PositiveIntegerField("ترتیب", default=0)

    class Meta:
        verbose_name = "مورد"
        verbose_name_plural = "موارد"
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return self.heading


class TrustBadge(models.Model):
    """The "7-day returns / fast delivery / ..." items in the footer, product and about pages."""

    class Icon(models.TextChoices):
        RETURN = "return", "بازگشت کالا"
        TRUCK = "truck", "ارسال"
        SHIELD = "shield", "پرداخت امن"
        BADGE = "badge", "ضمانت"
        PHONE = "phone", "پشتیبانی"
        CLOCK = "clock", "زمان"

    site = models.ForeignKey(SiteSettings, on_delete=models.CASCADE, related_name="trust_badges")
    icon = models.CharField("آیکون", max_length=20, choices=Icon.choices, default=Icon.BADGE)
    title = models.CharField("عنوان", max_length=60)
    subtitle = models.CharField("توضیح کوتاه", max_length=80, blank=True)
    is_active = models.BooleanField("فعال", default=True)
    order = models.PositiveIntegerField("ترتیب", default=0)

    class Meta:
        verbose_name = "مزیت فروشگاه"
        verbose_name_plural = "مزیت‌های فروشگاه"
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return self.title


class FooterColumn(models.Model):
    site = models.ForeignKey(SiteSettings, on_delete=models.CASCADE, related_name="footer_columns")
    title = models.CharField("عنوان ستون", max_length=60)
    order = models.PositiveIntegerField("ترتیب", default=0)

    class Meta:
        verbose_name = "ستون پاورقی"
        verbose_name_plural = "ستون‌های پاورقی"
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return self.title


class FooterLink(models.Model):
    column = models.ForeignKey(FooterColumn, on_delete=models.CASCADE, related_name="links")
    title = models.CharField("عنوان", max_length=60)
    url = models.CharField("لینک", max_length=300, help_text="مسیر داخل سایت مثل /faq یا آدرس کامل سایت دیگر")
    order = models.PositiveIntegerField("ترتیب", default=0)

    class Meta:
        verbose_name = "لینک"
        verbose_name_plural = "لینک‌ها"
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return self.title


class Banner(TimeStampedModel):
    """Home page slides: an image (JPG/PNG/GIF) or a silent looping video."""

    title = models.CharField("عنوان", max_length=150, blank=True)
    subtitle = models.CharField("زیرعنوان", max_length=250, blank=True)
    image = models.ImageField(
        "تصویر دسکتاپ",
        upload_to="banners/",
        blank=True,
        help_text="JPG، PNG یا GIF متحرک. اگر ویدیو هم بگذارید، این تصویر تا بارگذاری ویدیو نمایش داده می‌شود.",
    )
    image_mobile = models.ImageField("تصویر موبایل", upload_to="banners/", null=True, blank=True)
    video = models.FileField(
        "ویدیو",
        upload_to="banners/videos/",
        blank=True,
        validators=[FileExtensionValidator(["mp4", "webm"]), validate_video_size],
        help_text=f"MP4 یا WebM، حداکثر {MAX_VIDEO_MB} مگابایت. بدون صدا و به‌صورت تکرارشونده پخش می‌شود.",
    )
    link = models.CharField(
        "لینک (مسیر نسبی سایت)",
        max_length=300,
        blank=True,
        help_text="با کلیک روی بنر باز می‌شود، مثلاً /collection/spring",
    )
    is_active = models.BooleanField("فعال", default=True)
    order = models.PositiveIntegerField("ترتیب", default=0)

    class Meta:
        verbose_name = "بنر"
        verbose_name_plural = "بنرها"
        ordering = ["order", "-created_at"]

    def __str__(self) -> str:
        return self.title or f"بنر #{self.pk}"

    def clean(self) -> None:
        if not self.image and not self.video:
            raise ValidationError("یک تصویر یا یک ویدیو برای بنر انتخاب کنید.")
