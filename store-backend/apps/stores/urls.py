from django.urls import path

from .views import StoreListView

urlpatterns = [path("stores/", StoreListView.as_view(), name="stores")]
