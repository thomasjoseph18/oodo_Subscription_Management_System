import json
from decimal import Decimal

from rest_framework import mixins, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.customers.access import scope_to_user
from apps.invoices.models import Invoice
from common import razorpay_client
from common.permissions import IsTeam

from . import services
from .models import Payment

MANUAL_METHODS = [choice for choice in Payment.METHODS if choice[0] != "online_gateway"]


class PaymentSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    invoice_numbers = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = ["id", "reference", "customer", "customer_name", "invoice_numbers", "method", "amount", "paid_on", "notes", "status"]

    def get_invoice_numbers(self, obj):
        return ", ".join(allocation.invoice.number for allocation in obj.allocations.all())


class AllocationInputSerializer(serializers.Serializer):
    invoice = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal("0.01"))


class PaymentInputSerializer(serializers.Serializer):
    invoice = serializers.IntegerField(required=False)
    amount = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal("0.01"), required=False)
    allocations = AllocationInputSerializer(many=True, required=False)
    method = serializers.ChoiceField(choices=MANUAL_METHODS)
    paid_on = serializers.DateField()
    notes = serializers.CharField(required=False, allow_blank=True, default="")

    def validate(self, attrs):
        if attrs.get("allocations"):
            attrs["allocations"] = [(item["invoice"], item["amount"]) for item in attrs["allocations"]]
        elif attrs.get("invoice") and attrs.get("amount"):
            attrs["allocations"] = [(attrs["invoice"], attrs["amount"])]
        else:
            raise serializers.ValidationError({"amount": ["Give an invoice and an amount."]})
        ids = [invoice_id for invoice_id, _ in attrs["allocations"]]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError({"allocations": ["Each invoice can appear only once."]})
        if Invoice.objects.filter(pk__in=ids).count() != len(ids):
            raise serializers.ValidationError({"invoice": ["Invoice not found."]})
        attrs.pop("invoice", None)
        attrs.pop("amount", None)
        return attrs


class PaymentViewSet(mixins.CreateModelMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = PaymentSerializer
    search_fields = ["reference", "customer__name", "notes"]
    ordering_fields = ["reference", "method", "amount", "paid_on", "status"]
    filterset_fields = ["method", "status", "customer"]

    def get_permissions(self):
        return [IsTeam()] if self.action == "create" else [IsAuthenticated()]

    def get_queryset(self):
        queryset = Payment.objects.select_related("customer").prefetch_related("allocations__invoice")
        return scope_to_user(queryset, self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = PaymentInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(PaymentSerializer(services.record_payment(request.user, **serializer.validated_data)).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"], url_path="razorpay/order")
    def razorpay_order(self, request):
        invoice_id = serializers.IntegerField().run_validation(request.data.get("invoice"))
        invoice = scope_to_user(Invoice.objects.exclude(status="draft"), request.user).filter(pk=invoice_id).first()
        if invoice is None:
            return Response({"error": {"code": "not_found", "message": "Invoice not found.", "details": {}}}, status=404)
        return Response(services.create_gateway_order(request.user, invoice.id))

    @action(detail=False, methods=["post"], url_path="razorpay/verify")
    def razorpay_verify(self, request):
        payment = services.verify_checkout(
            request.data.get("razorpay_order_id"), request.data.get("razorpay_payment_id"), request.data.get("razorpay_signature"),
        )
        return Response(PaymentSerializer(payment).data)


class RazorpayWebhookView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = []

    def get_authenticate_header(self, request):
        return "Signature"

    def post(self, request):
        body = request.body
        if not razorpay_client.verify_webhook_signature(body, request.headers.get("X-Razorpay-Signature")):
            raise AuthenticationFailed("Invalid signature.")
        applied = services.handle_webhook(request.headers.get("X-Razorpay-Event-Id", ""), json.loads(body))
        return Response({"status": "applied" if applied else "duplicate"})
