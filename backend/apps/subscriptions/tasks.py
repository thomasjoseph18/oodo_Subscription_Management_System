from celery import shared_task

from . import services


@shared_task
def daily_subscription_task():
    return {
        "activated": services.activate_due(),
        "closed": services.close_expired(),
        "reminded": services.remind_upcoming(),
    }
