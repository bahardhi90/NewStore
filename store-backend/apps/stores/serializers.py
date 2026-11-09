from rest_framework import serializers

from .models import Store


class StoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = ["id", "name", "city", "address", "phone", "hours", "latitude", "longitude", "image"]
