from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Group, Member
from django.shortcuts import get_object_or_404


class UserIsInGroup(LoginRequiredMixin, UserPassesTestMixin):
    redirect_field_name = None
    target_group = None
    owner_permission = False

    def test_func(self):
        self.target_group = get_object_or_404(Group, id=self.kwargs['group_id'])
        try:
            membership = Member.objects.get(user=self.request.user, group=self.target_group)
        except Member.DoesNotExist:
            return False
        return (self.owner_permission and membership.rank == Member.Rank.owner) or not self.owner_permission
