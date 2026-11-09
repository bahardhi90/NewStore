from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from apps.core import messages as msg
from apps.core.exceptions import StoreError
from apps.core.utils import client_ip
from apps.notifications.events import SmsEvent, customer_name
from apps.notifications.services import notify

from . import otp
from .models import Address, User
from .serializers import (
    AddressSerializer,
    AuthTokensSerializer,
    OtpRequestResponseSerializer,
    OtpRequestSerializer,
    OtpVerifySerializer,
    RefreshSerializer,
    UserSerializer,
)


class OtpRequestView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes: list = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "otp"

    @extend_schema(tags=["auth"], request=OtpRequestSerializer, responses=OtpRequestResponseSerializer)
    def post(self, request):
        serializer = OtpRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = otp.request_otp(serializer.validated_data["phone"], client_ip(request))
        return Response({"detail": msg.OTP_SENT, "expires_in": result.expires_in, "resend_in": result.resend_in})


class OtpVerifyView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes: list = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "otp"

    @extend_schema(tags=["auth"], request=OtpVerifySerializer, responses=AuthTokensSerializer)
    def post(self, request):
        serializer = OtpVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data["phone"]
        otp.verify_otp(phone, serializer.validated_data["code"])

        with transaction.atomic():
            user = User.objects.filter(phone=phone).first()
            is_new = user is None
            if is_new:
                user = User.objects.create_user(phone=phone)
                notify(SmsEvent.WELCOME, phone, {"name": customer_name(user)})
        if not user.is_active:
            raise StoreError(msg.USER_INACTIVE, "permission_denied", status_code=403)

        refresh = RefreshToken.for_user(user)
        data = {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": UserSerializer(user).data,
            "is_new": is_new,
        }
        return Response(data)


@extend_schema(tags=["auth"])
class RefreshView(TokenRefreshView):
    """Rotates the refresh token; the old one is blacklisted."""


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(tags=["auth"], request=RefreshSerializer, responses={204: None})
    def post(self, request):
        serializer = RefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            RefreshToken(serializer.validated_data["refresh"]).blacklist()
        except TokenError:
            pass  # already invalid/blacklisted: logging out is still successful
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=["me"])
class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "patch", "head", "options"]

    def get_object(self):
        return self.request.user


@extend_schema(tags=["me"])
class AddressViewSet(viewsets.ModelViewSet):
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Address.objects.none()
        return Address.objects.filter(user=self.request.user)

    @transaction.atomic
    def perform_destroy(self, instance: Address) -> None:
        was_default = instance.is_default
        user = instance.user
        instance.delete()
        if was_default:
            next_address = user.addresses.order_by("-created_at").first()
            if next_address:
                next_address.is_default = True
                next_address.save(update_fields=["is_default"])
