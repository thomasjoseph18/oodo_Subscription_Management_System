from django.db import transaction

from .models import Notification
from .tasks import send_email_task


def notify(user, event, title, body="", email=True):
    """In-app notification plus email, sent only after the transaction commits
    so a rollback never leaves a stray email."""
    if user is None:
        return None
    note = Notification.objects.create(user=user, event=event, title=title, body=body)
    if email:
        transaction.on_commit(lambda: send_email_task.delay(user.email, title, body or title))
    return note
