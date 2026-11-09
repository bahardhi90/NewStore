import logging

from celery import shared_task

from .providers import SmsError
from .services import send_now

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_event_sms(self, event: str, phone: str, values: dict[str, str]) -> None:
    try:
        send_now(event, phone, values)
    except SmsError as exc:
        if exc.retry and self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=30 * 2**self.request.retries) from exc
        logger.error("SMS %s to %s failed: %s", event, phone, exc)
