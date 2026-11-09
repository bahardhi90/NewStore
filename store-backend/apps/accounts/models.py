from typing import Any

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel
from apps.core.utils import normalize_phone, validate_phone, validate_postal_code


class UserManager(BaseUserManager["User"]):
    use_in_migrations = True

    def create_user(self, phone: str, password: str | None = None, **extra: Any) -> "User":
        phone = normalize_phone(phone)
        validate_phone(phone)
        user = self.model(phone=phone, **extra)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, phone: str, password: str | None = None, **extra: Any) -> "User":
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        return self.create_user(phone, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    """Customers log in with phone + OTP (no password). Staff use a password for /admin/."""

    phone = models.CharField("شماره موبایل", max_length=11, unique=True, validators=[validate_phone])
    first_name = models.CharField("نام", max_length=50, blank=True)
    last_name = models.CharField("نام خانوادگی", max_length=50, blank=True)
    email = models.EmailField("ایمیل", blank=True, null=True)
    is_active = models.BooleanField("فعال", default=True)
    is_staff = models.BooleanField("کارمند", default=False)
    date_joined = models.DateTimeField("تاریخ عضویت", default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS: list[str] = []

    class Meta:
        verbose_name = "کاربر"
        verbose_name_plural = "کاربران"

    def __str__(self) -> str:
        return self.get_full_name() or self.phone

    def get_full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self) -> str:
        return self.first_name or self.phone


class Address(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses", verbose_name="کاربر")
    title = models.CharField("عنوان", max_length=50)
    receiver_name = models.CharField("نام گیرنده", max_length=100)
    receiver_phone = models.CharField("موبایل گیرنده", max_length=11, validators=[validate_phone])
    province = models.CharField("استان", max_length=50)
    city = models.CharField("شهر", max_length=50)
    postal_code = models.CharField("کد پستی", max_length=10, validators=[validate_postal_code])
    address_line = models.TextField("آدرس")
    is_default = models.BooleanField("پیش‌فرض", default=False)

    class Meta:
        verbose_name = "آدرس"
        verbose_name_plural = "آدرس‌ها"
        ordering = ["-is_default", "-created_at"]

    def __str__(self) -> str:
        return f"{self.title} - {self.city}"

    def as_snapshot(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "receiver_name": self.receiver_name,
            "receiver_phone": self.receiver_phone,
            "province": self.province,
            "city": self.city,
            "postal_code": self.postal_code,
            "address_line": self.address_line,
            "is_default": self.is_default,
        }
