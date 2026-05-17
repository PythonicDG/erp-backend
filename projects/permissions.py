from rest_framework import permissions

class CanCreateProject(permissions.BasePermission):
    """
    Permission to allow only Employee, Supervisor, and Admin to create projects.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check roles (Assuming roles are stored in request.user.role)
        # Roles in this system: ADMIN, SUPERVISOR, EMPLOYEE
        allowed_roles = ['ADMIN', 'SUPERVISOR', 'EMPLOYEE']
        return request.user.role in allowed_roles

class IsAdminUser(permissions.BasePermission):
    """
    Permission to allow only Admin role users.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'ADMIN'
