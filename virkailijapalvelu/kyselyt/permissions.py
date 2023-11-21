from rest_framework.permissions import BasePermission

from kyselyt.constants import SERVICE_USER_GROUP, SERVICE_USER_ACTIONS


class ServiceUserAccessPermission(BasePermission):
    message = f"User is not in group '{SERVICE_USER_GROUP}'."

    def has_permission(self, request, view):
        if view.action not in SERVICE_USER_ACTIONS:
            return True
        elif SERVICE_USER_GROUP in [group.name for group in request.user.groups.all()]:
            return True
        return False
