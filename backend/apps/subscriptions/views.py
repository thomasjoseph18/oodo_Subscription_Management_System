from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.customers.access import ensure_can_manage, scope_to_user
from common.permissions import CUSTOMER, IsTeam

from . import services
from .models import PlanChangeRequest, Subscription
from .serializers import PlanChangeSerializer, SubscriptionCreateSerializer, SubscriptionEventSerializer, SubscriptionSerializer


class SubscriptionViewSet(mixins.CreateModelMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = SubscriptionSerializer
    search_fields = ["number", "customer__name", "plan__name"]
    ordering_fields = ["number", "next_billing_date", "expiry_date", "status", "start_date"]
    filterset_fields = ["status", "customer", "plan"]
    customer_actions = ("list", "retrieve", "events", "pause", "resume", "renew", "close", "plan_change")

    def get_permissions(self):
        return [IsAuthenticated()] if self.action in self.customer_actions else [IsTeam()]

    def get_queryset(self):
        queryset = Subscription.objects.select_related("customer", "plan", "payment_term").prefetch_related("lines")
        return scope_to_user(queryset, self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = SubscriptionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ensure_can_manage(request.user, serializer.validated_data["customer"])
        subscription = services.create_subscription(request.user, **serializer.validated_data)
        return Response(SubscriptionSerializer(subscription).data, status=status.HTTP_201_CREATED)

    def _run(self, operation):
        subscription = self.get_object()
        if self.request.user.role != CUSTOMER:
            ensure_can_manage(self.request.user, subscription.customer)
        return Response(SubscriptionSerializer(operation(self.request.user, subscription)).data)

    @action(detail=True, methods=["post"])
    def quote(self, request, pk=None):
        return self._run(services.quote)

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        return self._run(services.confirm)

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        return self._run(services.activate)

    @action(detail=True, methods=["post"])
    def pause(self, request, pk=None):
        return self._run(services.pause)

    @action(detail=True, methods=["post"])
    def resume(self, request, pk=None):
        return self._run(services.resume)

    @action(detail=True, methods=["post"])
    def renew(self, request, pk=None):
        return self._run(services.renew)

    @action(detail=True, methods=["post"])
    def close(self, request, pk=None):
        return self._run(services.close)

    @action(detail=True, methods=["get"], pagination_class=None, filter_backends=[])
    def events(self, request, pk=None):
        return Response(SubscriptionEventSerializer(self.get_object().events.select_related("actor"), many=True).data)

    @action(detail=True, methods=["post"], url_path="plan-change")
    def plan_change(self, request, pk=None):
        subscription = self.get_object()
        serializer = PlanChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        change = services.request_plan_change(request.user, subscription, serializer.validated_data["plan"])
        return Response(PlanChangeSerializer(change).data, status=status.HTTP_201_CREATED)


class PlanChangeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PlanChangeRequest.objects.select_related("plan", "subscription")
    serializer_class = PlanChangeSerializer
    permission_classes = [IsTeam]
    filterset_fields = ["status"]

    def _decide(self, approve):
        change = self.get_object()
        ensure_can_manage(self.request.user, change.subscription.customer)
        return Response(PlanChangeSerializer(services.decide_plan_change(self.request.user, change, approve)).data)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        return self._decide(True)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        return self._decide(False)
