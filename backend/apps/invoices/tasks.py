from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMessage

from common.pdf import render_pdf

from . import services
from .models import Invoice


@shared_task
def run_billing_task():
    return services.run_billing().id


@shared_task
def overdue_reminders_task():
    return services.send_overdue_reminders()


@shared_task(ignore_result=True)
def send_invoice_task(invoice_id):
    invoice = Invoice.objects.select_related("customer").get(pk=invoice_id)
    message = EmailMessage(
        f"Invoice {invoice.number} from Brightloop",
        f"Your invoice for ₹{invoice.total} is attached. It is due on {invoice.due_date}.",
        settings.DEFAULT_FROM_EMAIL,
        [invoice.customer.email],
    )
    message.attach(f"{invoice.number}.pdf", render_pdf("documents/invoice.html", {"doc": invoice}), "application/pdf")
    message.send()
