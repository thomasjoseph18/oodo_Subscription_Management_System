from celery import shared_task

from .services import notify_expiring


@shared_task
def discount_expiry_task():
    return notify_expiring()
