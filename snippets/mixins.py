from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Group, Member
from django.shortcuts import get_object_or_404
from .types import Types


class UserIsInGroup(LoginRequiredMixin, UserPassesTestMixin):
    redirect_field_name = None
    target_group = None
    permissions = Types.ALL

    def test_func(self):
        self.target_group = get_object_or_404(Group, id=self.kwargs['group_id'])
        try:
            membership = Member.objects.get(user=self.request.user, group=self.target_group)
        except Member.DoesNotExist:
            return False
        return self.permissions == Types.ALL or membership.rank in self.permissions
