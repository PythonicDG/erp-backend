from rest_framework.permissions import BasePermission
from .models import UserRole


class IsAdmin(BasePermission):
    """Allows access only to admin users."""
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in [UserRole.ADMIN, UserRole.SUPERADMIN]
        )


class IsSupervisor(BasePermission):
    """Allows access only to supervisor users."""
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == UserRole.SUPERVISOR
        )


class IsEmployee(BasePermission):
    """Allows access only to employee users."""
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == UserRole.EMPLOYEE
        )


class IsAdminOrSupervisor(BasePermission):
    """Allows access to admin or supervisor users."""
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in [UserRole.ADMIN, UserRole.SUPERADMIN, UserRole.SUPERVISOR]
        )


class IsOwnerOrAdmin(BasePermission):
    """Allows access to the object owner or admin users."""
    def has_object_permission(self, request, view, obj):
        if request.user.role in [UserRole.ADMIN, UserRole.SUPERADMIN]:
            return True
        return obj.id == request.user.id


def has_role(user, *roles):
    """
    Utility function to check if a user has any of the given roles.

    Usage:
        if has_role(request.user, UserRole.ADMIN, UserRole.SUPERVISOR):
            # do something
    """
    return user.is_authenticated and user.role in roles
