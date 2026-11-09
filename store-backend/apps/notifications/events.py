"""SMS events: when a message is sent, which variables its text may use, and their sample values."""

import re
from dataclasses import dataclass, field

from django.db import models

from apps.core.utils import fa_digits

PLACEHOLDER_RE = re.compile(r"\{(\w+)\}")
EMPTY_VALUE = "-"  # Melipayamak rejects empty variables


class SmsEvent(models.TextChoices):
    OTP = "otp", "کد ورود / ثبت‌نام"
    WELCOME = "welcome", "خوش‌آمدگویی پس از ثبت‌نام"
    ORDER_PAID = "order_paid", "پرداخت موفق سفارش"
    ORDER_SHIPPED = "order_shipped", "ارسال سفارش"
    ORDER_DELIVERED = "order_delivered", "تحویل سفارش"
    ORDER_CANCELLED = "order_cancelled", "لغو سفارش"


@dataclass(frozen=True)
class EventSpec:
    variables: dict[str, str]  # name -> what it means (shown in admin)
    default_text: str
    default_active: bool = False
    sample: dict[str, str] = field(default_factory=dict)


COMMON = {"site": "نام سایت"}
CUSTOMER = {"name": "نام مشتری (اگر ثبت نشده باشد: «مشتری»)"}
ORDER = {
    **CUSTOMER,
    "order_number": "شماره سفارش",
    "products": "نام کالا (اگر چند کالا باشد: «شلوار راه‌راه و ۲ کالای دیگر»)",
    "total": "مبلغ پرداختی (تومان، بدون کلمه تومان)",
}
ORDER_SAMPLE = {"name": "علی", "order_number": "1405-000123", "products": "شلوار راه‌راه", "total": "۱٬۲۵۰٬۰۰۰"}

SPECS: dict[str, EventSpec] = {
    SmsEvent.OTP: EventSpec(
        variables={**COMMON, "code": "کد تأیید"},
        default_text="کد ورود شما به {site}: {code}",
        default_active=True,
        sample={"code": "12345"},
    ),
    SmsEvent.WELCOME: EventSpec(
        variables={**COMMON, **CUSTOMER},
        default_text="{name} عزیز، به {site} خوش آمدید.",
        sample={"name": "علی"},
    ),
    SmsEvent.ORDER_PAID: EventSpec(
        variables={**COMMON, **ORDER},
        default_text="{name} عزیز، خرید {products} با موفقیت انجام شد. شماره سفارش: {order_number}",
        default_active=True,
        sample=ORDER_SAMPLE,
    ),
    SmsEvent.ORDER_SHIPPED: EventSpec(
        variables={**COMMON, **ORDER, "tracking_code": "کد رهگیری مرسوله"},
        default_text="{name} عزیز، سفارش {order_number} ارسال شد. کد رهگیری مرسوله: {tracking_code}",
        sample={**ORDER_SAMPLE, "tracking_code": "123456789012345678"},
    ),
    SmsEvent.ORDER_DELIVERED: EventSpec(
        variables={**COMMON, **ORDER},
        default_text="{name} عزیز، سفارش {order_number} تحویل شد. از خرید شما سپاسگزاریم.",
        sample=ORDER_SAMPLE,
    ),
    SmsEvent.ORDER_CANCELLED: EventSpec(
        variables={**COMMON, **ORDER},
        default_text="{name} عزیز، سفارش {order_number} لغو شد.",
        sample=ORDER_SAMPLE,
    ),
}


def placeholders(text: str) -> list[str]:
    """Variable names in order of first appearance (each one becomes {0}, {1}, ... in Melipayamak)."""
    names: list[str] = []
    for name in PLACEHOLDER_RE.findall(text or ""):
        if name not in names:
            names.append(name)
    return names


def to_pattern_text(text: str) -> str:
    """The same text with numbered variables, as Melipayamak expects it."""
    order = placeholders(text)
    return PLACEHOLDER_RE.sub(lambda m: "{%d}" % order.index(m.group(1)), text or "")


def render(text: str, values: dict[str, str]) -> str:
    return PLACEHOLDER_RE.sub(lambda m: str(values.get(m.group(1)) or EMPTY_VALUE), text or "")


def format_toman(amount: int) -> str:
    return fa_digits(f"{amount:,}".replace(",", "٬"))


def customer_name(user) -> str:
    return (getattr(user, "first_name", "") or "").strip() or "مشتری"


def order_values(order) -> dict[str, str]:
    titles = [item.title for item in order.items.all()]
    products = titles[0] if titles else ""
    if len(titles) > 1:
        products = f"{products} و {fa_digits(len(titles) - 1)} کالای دیگر"
    return {
        "name": customer_name(order.user),
        "order_number": order.number,
        "products": products,
        "total": format_toman(order.total),
        "tracking_code": order.tracking_code or "",
    }


STATUS_EVENTS = {
    "paid": SmsEvent.ORDER_PAID,
    "shipped": SmsEvent.ORDER_SHIPPED,
    "delivered": SmsEvent.ORDER_DELIVERED,
    "cancelled": SmsEvent.ORDER_CANCELLED,
}
