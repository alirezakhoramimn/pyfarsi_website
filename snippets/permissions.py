from rest_framework.permissions import BasePermission
from .models import Member


class UserIsGroupAdmin(BasePermission):
    def has_permission(self, request, view):
        try:
            Member.objects.get(rank__in=(Member.Rank.admim, Member.Rank.owner), group__id=view.kwargs.group_id)
        except Member.DoesNotExist:
            return False
        return True
