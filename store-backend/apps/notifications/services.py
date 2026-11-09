"""Sending automatic SMS messages. Call `notify()` / `notify_order()`; they send after the DB transaction commits."""

import logging

from django.db import transaction

from .events import EMPTY_VALUE, SPECS, STATUS_EVENTS, SmsEvent, order_values, placeholders, render
from .models import SmsLog, SmsProvider, SmsSettings, SmsTemplate
from .providers import SmsError, send_console, send_melipayamak

logger = logging.getLogger(__name__)
SECRET_VARIABLES = ("code",)  # never stored in the SMS log


def _site_name() -> str:
    from apps.content.models import SiteSettings

    return SiteSettings.load().brand_name


def _template(event: str) -> SmsTemplate | None:
    template = SmsTemplate.objects.filter(event=event).first()
    if template is None and event == SmsEvent.OTP:  # login must always work
        template = SmsTemplate(event=event, text=SPECS[event].default_text, is_active=True)
    if template is None or not (template.is_active or event == SmsEvent.OTP):
        return None
    return template


def send_now(event: str, phone: str, values: dict[str, str], template: SmsTemplate | None = None) -> SmsLog | None:
    """Send immediately. Returns the log row, or None when this event's SMS is switched off. Raises SmsError."""
    template = template or _template(event)
    if template is None:
        return None
    values = {"site": _site_name(), **values}
    config = SmsSettings.load()
    hidden = {**values, **{name: "*****" for name in SECRET_VARIABLES if name in values}}
    log = SmsLog(event=event, phone=phone, text=render(template.text, hidden), provider=config.provider)
    try:
        if config.provider == SmsProvider.MELIPAYAMAK:
            if template.body_id is None:
                raise SmsError("کد پترن این پیامک در پنل مدیریت وارد نشده است.")
            log.detail = send_melipayamak(
                url=config.api_url,
                username=config.username,
                password=config.password,
                to=phone,
                body_id=template.body_id,
                values=[str(values.get(name) or EMPTY_VALUE) for name in placeholders(template.text)],
            )
        else:
            log.detail = send_console(to=phone, text=render(template.text, values))
    except SmsError as exc:
        log.status, log.detail = SmsLog.Status.FAILED, str(exc)[:300]
        log.save()
        raise
    log.status = SmsLog.Status.SENT
    log.save()
    return log


def notify(event: str, phone: str, values: dict[str, str] | None = None) -> None:
    """Queue the SMS for `event` once the current transaction is committed."""
    from .tasks import send_event_sms

    payload = {key: str(value) for key, value in (values or {}).items()}
    transaction.on_commit(lambda: send_event_sms.delay(event, phone, payload))


def notify_order(order) -> None:
    """SMS for the order's current status (paid / shipped / delivered / cancelled), if that SMS is on."""
    event = STATUS_EVENTS.get(order.status)
    if event and SmsTemplate.objects.filter(event=event, is_active=True).exists():
        notify(event, order.user.phone, order_values(order))
