from drf_spectacular.utils import extend_schema
from rest_framework import generics

from .models import Store
from .serializers import StoreSerializer


@extend_schema(tags=["stores"])
class StoreListView(generics.ListAPIView):
    serializer_class = StoreSerializer
    pagination_class = None
    queryset = Store.objects.filter(is_active=True)
