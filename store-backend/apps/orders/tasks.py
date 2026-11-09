import logging

from celery import shared_task

from . import services

logger = logging.getLogger(__name__)


@shared_task
def cancel_expired_orders() -> int:
    count = services.cancel_expired_orders()
    if count:
        logger.info("Auto-cancelled %s unpaid orders", count)
    return count
