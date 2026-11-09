from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import AddressViewSet, LogoutView, MeView, OtpRequestView, OtpVerifyView, RefreshView

router = SimpleRouter()
router.register("me/addresses", AddressViewSet, basename="address")

urlpatterns = [
    path("auth/otp/request/", OtpRequestView.as_view(), name="otp-request"),
    path("auth/otp/verify/", OtpVerifyView.as_view(), name="otp-verify"),
    path("auth/token/refresh/", RefreshView.as_view(), name="token-refresh"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("me/", MeView.as_view(), name="me"),
    *router.urls,
]
