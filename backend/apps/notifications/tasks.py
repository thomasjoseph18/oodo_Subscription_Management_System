from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail


@shared_task(ignore_result=True)
def send_email_task(to, subject, body):
    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [to], fail_silently=False)
