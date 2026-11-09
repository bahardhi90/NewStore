import re

from django.core.exceptions import ValidationError

from . import messages as msg

_DIGIT_MAP = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
_FA_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
PHONE_RE = re.compile(r"^09\d{9}$")


def to_en_digits(value: str) -> str:
    return (value or "").translate(_DIGIT_MAP)


def fa_digits(value: object) -> str:
    return str(value).translate(_FA_DIGITS)


def normalize_phone(value: str) -> str:
    """Accept 0912..., 912..., +98912..., 0098912... and Persian/Arabic digits."""
    phone = re.sub(r"[\s\-()]", "", to_en_digits(str(value)))
    if phone.startswith("+98"):
        phone = "0" + phone[3:]
    elif phone.startswith("0098"):
        phone = "0" + phone[4:]
    elif phone.startswith("98") and len(phone) == 12:
        phone = "0" + phone[2:]
    elif phone.startswith("9") and len(phone) == 10:
        phone = "0" + phone
    return phone


def validate_phone(value: str) -> None:
    if not PHONE_RE.match(value or ""):
        raise ValidationError(msg.PHONE_INVALID, code="invalid_phone")


def validate_postal_code(value: str) -> None:
    if not re.fullmatch(r"\d{10}", to_en_digits(value or "")):
        raise ValidationError(msg.POSTAL_CODE_INVALID, code="invalid_postal_code")


def client_ip(request) -> str:
    """Client IP. X-Forwarded-For is only trusted when NUM_PROXIES > 0 (behind Nginx)."""
    from django.conf import settings

    num_proxies = int(settings.REST_FRAMEWORK.get("NUM_PROXIES") or 0)
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if num_proxies and forwarded:
        parts = [p.strip() for p in forwarded.split(",") if p.strip()]
        if parts:
            return parts[-min(num_proxies, len(parts))]
    return request.META.get("REMOTE_ADDR", "") or "unknown"


def gregorian_to_jalali(gy: int, gm: int, gd: int) -> tuple[int, int, int]:
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    gy2 = gy + 1 if gm > 2 else gy
    days = 355666 + (365 * gy) + ((gy2 + 3) // 4) - ((gy2 + 99) // 100) + ((gy2 + 399) // 400) + gd + g_d_m[gm - 1]
    jy = -1595 + (33 * (days // 12053))
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365
    if days < 186:
        jm = 1 + (days // 31)
        jd = 1 + (days % 31)
    else:
        jm = 7 + ((days - 186) // 30)
        jd = 1 + ((days - 186) % 30)
    return jy, jm, jd
