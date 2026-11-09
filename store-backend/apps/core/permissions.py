from rest_framework.permissions import BasePermission


class IsOwner(BasePermission):
    """Object-level permission: obj.user must be the request user."""

    def has_object_permission(self, request, view, obj) -> bool:
        return getattr(obj, "user_id", None) == request.user.id
