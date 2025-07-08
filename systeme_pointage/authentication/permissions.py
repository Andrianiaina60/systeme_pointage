from rest_framework.permissions import BasePermission

class IsAdminByRoleOrStaff(BasePermission):
    """
    Autorise si user.role == 'admin' OU user.is_staff == True
    """
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if getattr(user, 'role', None) == 'admin':
            return True
        if user.is_staff:
            return True
        return False

class IsManagerUser(BasePermission):
    """
    Autorise si user.role == 'manager'
    """
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            print("IsManagerUser: utilisateur non authentifié")
            return False
        role = getattr(user, 'role', None)
        print(f"IsManagerUser: role = {role}")
        return role == 'manager'

class IsRHUser(BasePermission):
    """
    Autorise si user.role == 'rh'
    """
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            print("IsRHUser: utilisateur non authentifié")
            return False
        role = getattr(user, 'role', None)
        print(f"IsRHUser: role = {role}")
        return role == 'rh'
