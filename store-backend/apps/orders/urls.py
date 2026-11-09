from django.urls import path

from .views import MyOrderDetailView, MyOrderListView, OrderCreateView, ShippingMethodListView

urlpatterns = [
    path("shipping-methods/", ShippingMethodListView.as_view(), name="shipping-methods"),
    path("orders/", OrderCreateView.as_view(), name="order-create"),
    path("me/orders/", MyOrderListView.as_view(), name="my-orders"),
    path("me/orders/<int:pk>/", MyOrderDetailView.as_view(), name="my-order-detail"),
]
