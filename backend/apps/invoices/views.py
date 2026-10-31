import django_filters
from django.db.models import F, Q
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.customers.access import scope_to_user
from common.pdf import render_pdf
from common.permissions import CUSTOMER, IsAdmin, IsTeam

from . import services
from .models import BillingRun, BillingSettings, Invoice
from .serializers import BillingRunSerializer, BillingSettingsSerializer, InvoiceDetailSerializer, InvoiceSerializer
from .tasks import send_invoice_task


class InvoiceFilter(django_filters.FilterSet):
    payment_state = django_filters.CharFilter(method="filter_state")

    class Meta:
        model = Invoice
        fields = ["status", "customer", "subscription"]

    def filter_state(self, queryset, name, value):
        today = timezone.localdate()
        unsettled = Q(status="confirmed") & Q(amount_paid__lt=F("total"))
        conditions = {
            "paid": Q(status="paid"),
            "overdue": unsettled & Q(due_date__lt=today),
            "partial": unsettled & Q(amount_paid__gt=0) & Q(due_date__gte=today),
            "unpaid": unsettled & Q(amount_paid=0) & Q(due_date__gte=today),
        }
        return queryset.filter(conditions.get(value, Q()))


class InvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    filterset_class = InvoiceFilter
    search_fields = ["number", "customer__name", "subscription__number"]
    ordering_fields = ["number", "invoice_date", "due_date", "total", "status"]

    def get_permissions(self):
        return [IsAuthenticated()] if self.action in ("list", "retrieve", "pdf") else [IsTeam()]

    def get_serializer_class(self):
        return InvoiceDetailSerializer if self.action == "retrieve" else InvoiceSerializer

    def get_queryset(self):
        queryset = scope_to_user(Invoice.objects.select_related("customer", "subscription").prefetch_related("lines"), self.request.user)
        if self.request.user.role == CUSTOMER:
            queryset = queryset.exclude(status="draft")
        return queryset

    def _respond(self, invoice):
        return Response(InvoiceDetailSerializer(invoice).data)

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        return self._respond(services.confirm_invoice(request.user, self.get_object()))

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        return self._respond(services.cancel_invoice(request.user, self.get_object()))

    @action(detail=True, methods=["post"])
    def reissue(self, request, pk=None):
        return self._respond(services.reissue_invoice(request.user, self.get_object()))

    @action(detail=True, methods=["post"])
    def send(self, request, pk=None):
        invoice = self.get_object()
        send_invoice_task.delay(invoice.id)
        invoice.sent_at = timezone.now()
        invoice.save(update_fields=["sent_at"])
        return self._respond(invoice)

    @action(detail=True, methods=["get"])
    def pdf(self, request, pk=None):
        invoice = self.get_object()
        response = HttpResponse(render_pdf("documents/invoice.html", {"doc": invoice}), content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{invoice.number}.pdf"'
        return response


class BillingRunViewSet(mixins.CreateModelMixin, viewsets.ReadOnlyModelViewSet):
    queryset = BillingRun.objects.all()
    serializer_class = BillingRunSerializer
    permission_classes = [IsTeam]

    def create(self, request, *args, **kwargs):
        return Response(BillingRunSerializer(services.run_billing()).data, status=status.HTTP_201_CREATED)


class BillingSettingsView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        return Response(BillingSettingsSerializer(BillingSettings.load()).data)

    def patch(self, request):
        serializer = BillingSettingsSerializer(BillingSettings.load(), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
