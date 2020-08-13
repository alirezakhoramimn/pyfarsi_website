from django.views.generic import CreateView, ListView, DeleteView
from django.views.generic.detail import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.shortcuts import reverse, redirect
from . import forms, models, serializers, types, permissions
from account.serializers import GetUser
from .mixins import UserIsInGroup
from .functions import take_action
from django.utils.text import slugify
from rest_framework.generics import ListAPIView, CreateAPIView
from django.db.models import Q
from django.http import HttpResponseBadRequest, HttpResponseForbidden
from account.models import User


class Group(DetailView):
    template_name = 'snippets/group.html'
    model = models.Group

    def get_context_data(self, **kwargs):
        if self.request.user.is_authenticated:
            try:
                self.extra_context = {'member': models.Member.objects.get(user=request.user, group=self.object)}
            except models.Member.DoesNotExists:
                pass
        return super().get_context_data()


class Groups(ListView):
    template_name = 'snippets/groups.html'
    paginate_by = 15

    def get_queryset(self):
        result = models.Group.objects.all()
        if keyword := self.request.GET.get('q'):
            result = result.filter(Q(name__icontains=keyword) | Q(description__icontains=keyword))
        if types := self.request.GET.get('types'):
            types = types.split(', ')
            result = result.filter(type__in=types)
        return result


class Snippets(ListView):
    paginate_by = 15
    template_name = 'snippets/snippets.html'

    def get_queryset(self):
        if self.request.user.is_authenticated:
            memberships = self.request.user.member_user.select_related('group').filter(
                status=models.Member.Status.member, group__type=models.Group.Type.private
                )
            groups = [group_tuple[0] for membership_groups in memberships.values_list(
                'group__id'
                ) for group_tuple in membership_groups]
        else:
            groups = []
        keyword = self.request.GET.get('q', '')
        result = models.Snippet.objects.filter((
            Q(group__type=models.Group.Type.public) | Q(group__id__in=groups)
            ) & (Q(name__icontains=keyword) | Q(description__icontains=keyword)))
        if self.request.GET.get('groups'):
            groups = self.request.GET['groups'].split(', ')
            result = result.filter(group__id__in=groups)
        if self.request.GET.get('langs'):
            langs = self.request.GET['langs'].split(', ')
            result = result.filter(lang__in=langs)
        return result


class CreateGroup(LoginRequiredMixin, CreateView):
    model = models.Group
    fields = ('name', 'description', 'type', 'logo')
    template_name = 'snippets/create_group.html'

    def form_valid(self, form):
        self.object = form.save(False)
        self.object.slug = slugify(self.object.name, True)
        self.object.save()
        models.Member.objects.create(
            user=self.request.user, group=self.object, rank=models.Member.Rank.owner, status=models.Member.Rank.member
            )
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('snippets:group', kwargs={'pk': self.object.id, 'slug': self.object.slug})


class CreateSnippet(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    form_class = forms.Snippet
    template_name = 'snippets/create_snippet.html'
    redirect_field_name = None

    def get_success_url(self):
        return reverse('snippets:snippet', kwargs={'pk': self.object.id})

    def test_func(self):
        group = models.Group.objects.get(id=self.kwargs['group_id'])
        try:
            return models.Member.objects.get(user=self.request.user, group=group)
        except models.Member.DoesNotExists:
            return group.type == models.Group.Type.public

    def form_valid(self, form):
        self.object = form.save(False)
        self.object.user = self.request.user
        self.object.group = get_object_or_404(
            models.Member, user=self.request.user, group__id=self.kwargs['group_id']
        ).group
        self.object.slug = slugify(self.object.name, True)
        self.object.save()
        for screenshot in self.request.FILES.getlist('screenshots'):
            models.ScreenShot.objects.create(snippet=self.object, file=screenshot)
        return redirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        self.extra_context = {'group_id': self.kwargs['group_id']}
        return super().get_context_data(**kwargs)


class Snippet(UserPassesTestMixin, DetailView):
    model = models.Snippet
    template_name = 'snippets/snippet.html'
    redirect_field_name = None

    def test_func(self):
        try:
            return models.Member.objects.get(user=self.request.user, group=self.object.group)
        except models.Member.DoesNotExists:
            return self.object.group.type == models.Group.Type.public

    def get_context_data(self, **kwargs):
        self.extra_context = {'screenshots': self.object.screenshot_snippet.all()}
        return super().get_context_data(**kwargs)
    

class GetGroups(ListAPIView):
    serializer_class = serializers.GetGroup
    
    def get_queryset(self):
        return models.Group.objects.filter(
            Q(name__icontains=self.kwargs['q']), Q(description__icontains=self.kwargs['q'])
            )


class TelegramGroup(UserIsInGroup, DetailView):
    model = models.TelegramGroup
    template_name = 'snippets/telegram_group.html'


class TelegramGroups(UserIsInGroup, ListView):
    template_name = 'snippets/telegram_groups.html'
    paginate_by = 15

    def get_queryset(self):
        result = models.TelegramGroup.objects.filter(group=self.target_group)
        if self.request.GET.get('q'):
            try:
                chat_id = int(self.request.GET['q'])
            except ValueError:
                return result
            result = result.filter(chat_id__contains=chat_id)
        return result


class CreateTelegramGroup(UserIsInGroup, CreateView):
    model = models.TelegramGroup
    permissions = (models.Member.Rank.owner,)
    fields = ('chat_id', 'link')
    template_name = 'snippets/create_telegram_group.html'

    def form_valid(self, form):
        self.object = form.save(False)
        self.object.group = models.Group
        self.object.save()
        return reidrect(self.get_success_url())
    
    def get_success_url(self):
        return reverse('snippets:telegram_group', kwargs={'pk': self.object.group.id})


class DeleteTelegramGroup(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = models.TelegramGroup
    template_name = 'snippets/confirm_delete.html'
    
    def get_success_url(self):
        return reverse('snippets:telegram_groups', kwargs={'group_id': self.object.group.id, 'page': 1})
    
    def test_func(self):
        try:
            models.Member.objects.get(
                user=self.request.user, group=self.get_object().group, rank=models.Member.Rank.owner
                )
        except models.Member.DoesNotExists:
            return False
        return True


class GetUsers(ListAPIView):
    serializer_class = GetUser

    def get_queryset(self):
        return User.objects.filter(username__icontains=self.request.GET.get('q', ''))


class CreateUserInvites(CreateAPIView):
    serializer_class = serializers.CreateUserInvite
    permission_classes = (permissions.UserIsGroupAdmin,)
    pagination_class = None

    def get_serializer(self, *args, **kwargs):
        kwargs['many'] = True
        return super().get_serializer(*args, **kwargs)


@login_required
def join_group_with_link(request, invite_id):
    invite = get_object_or_404(models.InviteLink, invite_id=invite_id)
    member, created = models.Member.objects.get_or_create(
        user=request.user, group=invite.group, defaults={'status': models.Member.Status.member}
        )
    if created:
        invite.users_joined += 1
        invite.save()
    return redirect('snippets:group', pk=invite.group.id)


@login_required
def join_group(request, group_id):
    group = get_object_or_404(models.Group, id=group_id)
    status = models.Member.Status.pending if group.type is models.Group.Type.Private else \
        models.Member.Status.member
    models.Member.objects.get_or_create(
        user=request.user, group=group, defaults={'status': models.Member.Status.pending}
        )
    return redirect('snippets:group', pk=group.id)


@login_required
def take_actions(request, object_id: int, object_type: str, action: str):
    try:
        object_type = actions.Types(object_type)
        action = actions.Actions(action)
    except ValueError:
        return HttpResponseBadRequest('Invalid types !')
    if object_type is types.Types.SNIPPET:
        target_object = get_object_or_404(models.Snippet, id=object_id)
    else:
        target_object = get_object_or_404(models.Member, id=object_id)
    if target_object.user != request.user:
        try:
            models.Member.objects.get(
                user=request.user,
                rank__in=(models.Member.Rank.admin, models.Member.Rank.owner),
                group=snippet.group
                )
        except models.Member.DoesNotExists:
            return HttpResponseForbidden('You are not a group admin !')
        else:
            take_snippet_action(snippet, action)
    elif action is types.Actions.DELETE or object_type is not types.Types.Member:
        take_action(snippet, action)
    if action is types.Actions.CLOSE_SNIPPET:
        return redirect('snippets:snippet', pk=snippet_id)
    elif action is types.Actions.DELETE:
        if object_type is types.Types.SNIPPET:
            return redirect(f'{reverse("snippets:snippets", kwargs={"page": 1})}?groups={target_object.group.id}')
        else:
            return redirect('account:memberships', page=1)
    else:
        return redirect('snippets:members', group_id=target_object.group.id, page=1)
