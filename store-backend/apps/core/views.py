from django.core.cache import cache
from django.db import connection
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthView(APIView):
    """Liveness/readiness check for load balancers and docker healthchecks."""

    permission_classes = [AllowAny]
    authentication_classes: list = []
    throttle_classes: list = []

    @extend_schema(
        tags=["health"],
        responses=inline_serializer(
            "Health",
            {"status": serializers.CharField(), "db": serializers.BooleanField(), "cache": serializers.BooleanField()},
        ),
    )
    def get(self, request):
        db_ok = cache_ok = True
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        except Exception:  # noqa: BLE001
            db_ok = False
        try:
            cache.set("health:ping", "1", 5)
            cache_ok = cache.get("health:ping") == "1"
        except Exception:  # noqa: BLE001
            cache_ok = False
        ok = db_ok and cache_ok
        return Response(
            {"status": "ok" if ok else "degraded", "db": db_ok, "cache": cache_ok}, status=200 if ok else 503
        )
