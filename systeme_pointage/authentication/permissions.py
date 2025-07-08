from rest_framework.permissions import BasePermission

class IsAdminByRoleOrStaff(BasePermission):
    """
    Autorise si user.role == 'admin' OU user.is_staff == True
    """
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return getattr(user, 'role', None) == 'admin' or user.is_staff

class IsManagerUser(BasePermission):
    """
    Autorise si user.role == 'manager'
    """
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return getattr(user, 'role', None) == 'manager'

class IsRHUser(BasePermission):
    """
    Autorise si user.role == 'rh'
    """
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return getattr(user, 'role', None) == 'rh'

class IsRHOrAdmin(BasePermission):
    """
    Autorise si user.role == 'rh' ou 'admin' ou user.is_staff
    """
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return getattr(user, 'role', None) in ['rh', 'admin'] or user.is_staff
