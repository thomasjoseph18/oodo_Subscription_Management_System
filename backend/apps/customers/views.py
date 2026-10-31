from rest_framework import permissions, serializers
from rest_framework.decorators import action
from rest_framework.response import Response

from common.permissions import ADMIN, STAFF, IsCustomer, IsTeam
from common.viewsets import AuditedModelViewSet

from .access import ensure_can_manage
from .models import Customer


class CustomerSerializer(serializers.ModelSerializer):
    assigned_to_email = serializers.CharField(source="assigned_to.email", default=None, read_only=True)

    class Meta:
        model = Customer
        fields = ["id", "name", "email", "company", "phone", "gst_number", "billing_address", "assigned_to", "assigned_to_email", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate_assigned_to(self, value):
        request = self.context["request"]
        if value and value.role not in (ADMIN, STAFF):
            raise serializers.ValidationError("Only team members can be assigned.")
        if request.user.role != ADMIN and self.instance and value != self.instance.assigned_to:
            raise serializers.ValidationError("Only the admin can reassign customers.")
        return value


class CustomerBillingSerializer(serializers.ModelSerializer):
    """What customers may change themselves."""

    class Meta:
        model = Customer
        fields = ["id", "name", "email", "company", "phone", "gst_number", "billing_address"]
        read_only_fields = ["id", "email"]


class CustomerViewSet(AuditedModelViewSet):
    queryset = Customer.objects.select_related("assigned_to")
    serializer_class = CustomerSerializer
    permission_classes = [IsTeam]
    search_fields = ["name", "email", "company"]
    ordering_fields = ["name", "email", "company", "created_at"]
    filterset_fields = ["assigned_to"]

    def perform_create(self, serializer):
        user = self.request.user
        if user.role == STAFF:
            serializer.validated_data["assigned_to"] = user
        super().perform_create(serializer)

    def perform_update(self, serializer):
        ensure_can_manage(self.request.user, serializer.instance)
        super().perform_update(serializer)

    def perform_destroy(self, instance):
        ensure_can_manage(self.request.user, instance)
        super().perform_destroy(instance)

    @action(detail=False, methods=["get", "patch"], permission_classes=[permissions.IsAuthenticated, IsCustomer], filter_backends=[], pagination_class=None)
    def me(self, request):
        customer = Customer.objects.get(user=request.user)
        if request.method == "GET":
            return Response(CustomerBillingSerializer(customer).data)
        serializer = CustomerBillingSerializer(customer, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
