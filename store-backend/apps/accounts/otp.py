"""OTP service: codes are stored hashed in the cache (Redis) with a TTL."""

import hashlib
import hmac
import secrets
import time
from dataclasses import dataclass

from django.conf import settings
from django.core.cache import cache

from apps.core import messages as msg
from apps.core.exceptions import StoreError
from apps.core.utils import fa_digits
from apps.notifications.events import SmsEvent
from apps.notifications.services import notify


@dataclass(frozen=True)
class OtpRequestResult:
    expires_in: int
    resend_in: int


def _code_key(phone: str) -> str:
    return f"otp:code:{phone}"


def _cooldown_key(phone: str) -> str:
    return f"otp:cooldown:{phone}"


def _hash(phone: str, code: str) -> str:
    return hmac.new(settings.SECRET_KEY.encode(), f"{phone}:{code}".encode(), hashlib.sha256).hexdigest()


def _hit_limit(key: str, limit: int, window: int = 3600) -> bool:
    """Increment a counter; return True when it is over the limit."""
    cache.add(key, 0, window)
    try:
        count = cache.incr(key)
    except ValueError:
        cache.set(key, 1, window)
        count = 1
    return count > limit


def generate_code() -> str:
    return "".join(secrets.choice("0123456789") for _ in range(settings.OTP_LENGTH))


def request_otp(phone: str, ip: str) -> OtpRequestResult:
    now = time.time()
    cooldown_until = cache.get(_cooldown_key(phone))
    if cooldown_until and cooldown_until > now:
        wait = int(cooldown_until - now) + 1
        raise StoreError(
            msg.OTP_RESEND_WAIT.format(seconds=fa_digits(wait)),
            "throttled",
            status_code=429,
            errors={"retry_after": [str(wait)]},
        )

    if _hit_limit(f"otp:hour:phone:{phone}", settings.OTP_MAX_PER_HOUR_PHONE) or _hit_limit(
        f"otp:hour:ip:{ip}", settings.OTP_MAX_PER_HOUR_IP
    ):
        raise StoreError(msg.OTP_TOO_MANY, "throttled", status_code=429, errors={"retry_after": ["3600"]})

    code = generate_code()
    ttl = settings.OTP_TTL_SECONDS
    cache.set(_code_key(phone), {"hash": _hash(phone, code), "attempts": 0, "expires_at": now + ttl}, ttl)
    cache.set(_cooldown_key(phone), now + settings.OTP_RESEND_SECONDS, settings.OTP_RESEND_SECONDS)
    notify(SmsEvent.OTP, phone, {"code": code})
    return OtpRequestResult(expires_in=ttl, resend_in=settings.OTP_RESEND_SECONDS)


def verify_otp(phone: str, code: str) -> None:
    """Raise StoreError if the code is wrong/expired; consume the code on success."""
    key = _code_key(phone)
    data = cache.get(key)
    now = time.time()
    if not data or data["expires_at"] <= now:
        raise StoreError(msg.OTP_EXPIRED, "otp_expired", errors={"code": [msg.OTP_EXPIRED]})

    if data["attempts"] >= settings.OTP_MAX_ATTEMPTS:
        cache.delete(key)
        raise StoreError(msg.OTP_MAX_ATTEMPTS, "otp_max_attempts", status_code=429)

    if not hmac.compare_digest(data["hash"], _hash(phone, code)):
        data["attempts"] += 1
        if data["attempts"] >= settings.OTP_MAX_ATTEMPTS:
            cache.delete(key)
            raise StoreError(msg.OTP_MAX_ATTEMPTS, "otp_max_attempts", status_code=429)
        cache.set(key, data, max(1, int(data["expires_at"] - now)))
        raise StoreError(msg.OTP_INVALID, "otp_invalid", errors={"code": [msg.OTP_INVALID]})

    cache.delete(key)
