"""SMS services. Melipayamak: shared service line with an approved pattern (SOAP method SendByBaseNumber)."""

import logging
import re
from xml.sax.saxutils import escape

import httpx

logger = logging.getLogger(__name__)

SOAP_ACTION = '"http://tempuri.org/SendByBaseNumber"'
RESULT_RE = re.compile(r"<SendByBaseNumberResult>(.*?)</SendByBaseNumberResult>", re.S)

# Return codes from the Melipayamak docs (anything with more than 15 digits is the message id = success)
MELIPAYAMAK_ERRORS = {
    "-110": "به‌جای رمز عبور باید کلید API (ApiKey) پنل را وارد کنید.",
    "-109": "باید IP سرور را در پنل ملی پیامک به فهرست مجاز اضافه کنید.",
    "-108": "IP سرور به دلیل تلاش‌های ناموفق مسدود شده است.",
    "-10": "در متغیرها لینک وجود دارد (مجاز نیست).",
    "-7": "خطا در شماره فرستنده؛ با پشتیبانی ملی پیامک تماس بگیرید.",
    "-6": "خطای داخلی ملی پیامک.",
    "-5": "متغیرهای ارسالی با متن پترن هم‌خوانی ندارند (تعداد متغیرها را بررسی کنید).",
    "-4": "کد پترن اشتباه است یا هنوز تأیید نشده است.",
    "-3": "خط ارسال در سامانه تعریف نشده است.",
    "-2": "در هر بار فقط یک شماره مجاز است.",
    "-1": "دسترسی وب‌سرویس غیرفعال است؛ با پشتیبانی تماس بگیرید.",
    "0": "نام کاربری یا رمز عبور اشتباه است.",
    "2": "اعتبار پنل کافی نیست.",
    "6": "سامانه ملی پیامک در حال بروزرسانی است.",
    "7": "متن شامل کلمه فیلترشده است.",
    "10": "کاربر پنل فعال نیست.",
    "11": "ارسال نشد.",
    "12": "مدارک کاربری پنل کامل نیست.",
    "16": "شماره گیرنده یافت نشد.",
    "17": "متن پیامک خالی است.",
    "18": "شماره گیرنده معتبر نیست.",
    "19": "از سقف ارسال ساعتی عبور کرده‌اید.",
}
TEMPORARY_CODES = {"-6", "6", "11"}  # worth retrying later


class SmsError(Exception):
    def __init__(self, message: str, *, retry: bool = False) -> None:
        super().__init__(message)
        self.retry = retry


def _envelope(username: str, password: str, values: list[str], to: str, body_id: int) -> str:
    strings = "".join(f"<string>{escape(v)}</string>" for v in values)
    return (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"><soap:Body>'
        '<SendByBaseNumber xmlns="http://tempuri.org/">'
        f"<username>{escape(username)}</username><password>{escape(password)}</password>"
        f"<text>{strings}</text><to>{escape(to)}</to><bodyId>{int(body_id)}</bodyId>"
        "</SendByBaseNumber></soap:Body></soap:Envelope>"
    )


def send_melipayamak(*, url: str, username: str, password: str, to: str, body_id: int, values: list[str]) -> str:
    """Send one pattern message; returns Melipayamak's message id (recId)."""
    try:
        response = httpx.post(
            url,
            content=_envelope(username, password, values, to, body_id).encode(),
            headers={"Content-Type": "text/xml; charset=utf-8", "SOAPAction": SOAP_ACTION},
            timeout=15,
        )
    except httpx.HTTPError as exc:
        raise SmsError(f"ارتباط با ملی پیامک برقرار نشد: {exc.__class__.__name__}", retry=True) from exc

    match = RESULT_RE.search(response.text)
    if response.status_code >= 500 and not match:
        raise SmsError(f"خطای سرور ملی پیامک (HTTP {response.status_code})", retry=True)
    if not match:
        raise SmsError(f"پاسخ نامعتبر از ملی پیامک (HTTP {response.status_code})")

    result = match.group(1).strip()
    if len(result) > 15 and result.isdigit():
        return result
    reason = MELIPAYAMAK_ERRORS.get(result, "خطای ناشناخته")
    raise SmsError(f"کد {result}: {reason}", retry=result in TEMPORARY_CODES)


def send_console(*, to: str, text: str) -> str:
    """Development: nothing is sent; the message is printed in the server log."""
    logger.warning("[SMS] to=%s text=%s", to, text)
    print(f"\n===== SMS to {to}: {text} =====\n", flush=True)  # noqa: T201
    return "console"
