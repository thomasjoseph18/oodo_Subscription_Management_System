from django.http import HttpResponse
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.customers.access import ensure_can_manage, scope_to_user
from common.pdf import render_pdf
from common.permissions import IsTeam
from common.viewsets import AuditedModelViewSet

from . import services
from .models import Quotation, QuotationTemplate
from .serializers import QuotationCreateSerializer, QuotationSerializer, QuotationTemplateSerializer


class QuotationTemplateViewSet(AuditedModelViewSet):
    queryset = QuotationTemplate.objects.select_related("plan").prefetch_related("lines")
    serializer_class = QuotationTemplateSerializer
    permission_classes = [IsTeam]
    search_fields = ["name"]
    ordering_fields = ["name", "validity_days"]


class QuotationViewSet(mixins.CreateModelMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = QuotationSerializer
    search_fields = ["number", "customer__name"]
    ordering_fields = ["number", "valid_until", "total", "status"]
    filterset_fields = ["status", "customer"]

    def get_queryset(self):
        queryset = Quotation.objects.select_related("customer", "plan", "payment_term", "subscription").prefetch_related("lines")
        queryset = scope_to_user(queryset, self.request.user)
        if self.request.user.role == "customer":
            queryset = queryset.exclude(status="draft")
        return queryset

    def get_permissions(self):
        if self.action in ("list", "retrieve", "pdf", "accept", "reject"):
            return [IsAuthenticated()]
        return [IsTeam()]

    def create(self, request, *args, **kwargs):
        serializer = QuotationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ensure_can_manage(request.user, serializer.validated_data["customer"])
        quotation = services.create_quotation(request.user, **serializer.validated_data)
        return Response(QuotationSerializer(quotation).data, status=status.HTTP_201_CREATED)

    def _respond(self, quotation):
        return Response(QuotationSerializer(quotation).data)

    def _manageable(self):
        quotation = self.get_object()
        ensure_can_manage(self.request.user, quotation.customer)
        return quotation

    @action(detail=True, methods=["post"])
    def send(self, request, pk=None):
        return self._respond(services.send(request.user, self._manageable()))

    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        return self._respond(services.accept(request.user, self.get_object()))

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        return self._respond(services.reject(request.user, self.get_object()))

    @action(detail=True, methods=["post"])
    def convert(self, request, pk=None):
        from apps.subscriptions.serializers import SubscriptionSerializer
        from apps.subscriptions.services import create_from_quotation

        return Response(SubscriptionSerializer(create_from_quotation(request.user, self._manageable())).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"])
    def pdf(self, request, pk=None):
        quotation = self.get_object()
        response = HttpResponse(render_pdf("documents/quotation.html", {"doc": quotation}), content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{quotation.number}.pdf"'
        return response
