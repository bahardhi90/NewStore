from drf_spectacular.utils import extend_schema
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from . import services
from .models import PaymentMethod
from .serializers import (
    PaymentMethodSerializer,
    PaymentStartResponseSerializer,
    PaymentStartSerializer,
    PaymentVerifyQuerySerializer,
    PaymentVerifyResponseSerializer,
)


class PaymentMethodListView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(tags=["payments"], responses=PaymentMethodSerializer(many=True))
    def get(self, request):
        methods = PaymentMethod.objects.available()
        return Response(PaymentMethodSerializer(methods, many=True, context={"request": request}).data)


class PaymentStartView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "payments"

    @extend_schema(tags=["payments"], request=PaymentStartSerializer, responses=PaymentStartResponseSerializer)
    def post(self, request):
        serializer = PaymentStartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        started = services.start_payment(request.user, data["order_id"], data.get("method"))
        return Response({"redirect_url": started.redirect_url, "payment_id": started.payment.id})


class PaymentVerifyView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "payments"

    @extend_schema(
        tags=["payments"], parameters=[PaymentVerifyQuerySerializer], responses=PaymentVerifyResponseSerializer
    )
    def get(self, request):
        serializer = PaymentVerifyQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        result = services.verify_payment(
            data["Authority"], data["Status"], data.get("TrackingCode", ""), data.get("Type", "")
        )
        return Response(result)
