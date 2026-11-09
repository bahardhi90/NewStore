from django.urls import path

from .views import PaymentMethodListView, PaymentStartView, PaymentVerifyView

urlpatterns = [
    path("payments/methods/", PaymentMethodListView.as_view(), name="payment-methods"),
    path("payments/start/", PaymentStartView.as_view(), name="payment-start"),
    path("payments/verify/", PaymentVerifyView.as_view(), name="payment-verify"),
]
