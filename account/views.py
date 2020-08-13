from django.contrib.auth import views as auth_views
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.db.models import Q
from .models import Validation, User
from snippets.models import UserInvite, Member
from django.utils.html import strip_tags
from .tasks import remove_user
from .decorators import not_logged_in
from .mixins import NotLoggedIn
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import CreateView, UpdateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required]
from django.http import HttpResponseBadRequest
from . import models
from utils.functions import get_filters
from .forms import Register, Profile


class Login(auth_views.LoginView):
    template_name = 'account/login.html'
    success_url_allowed_hosts = settings.ALLOWED_HOSTS
    redirect_authenticated_user = True


class Logout(LoginRequiredMixin, auth_views.LogoutView):
    redirect_field_name = None
    template_name = 'account/logout.html'


class PasswordReset(auth_views.PasswordResetView):
    template_name = 'account/password_reset_form.html'
    success_url = 'account:password_reset_done'
    email_template_name = 'account/password_reset_email.html'


class PasswordResetDone(auth_views.PasswordResetDoneView):
    template_name = 'account/reset_done.html'


class PasswordResetConfirm(auth_views.PasswordResetConfirmView):
    template_name = 'account/password_reset_confirm.html'
    success_url = 'account:password_reset_complete'


class PasswordResetComplete(auth_views.PasswordResetCompleteView):
    template_name = 'account/password_reset_complete.html'


class RegisterView(NotLoggedIn, CreateView):
    form_class = Register
    template_name = 'account/register.html'
    success_url = 'account:register_complete'

    def form_valid(self, form):
        temp_user = form.save(False)
        temp_user.set_password(temp_user.password)
        temp_user.save()
        email_template = render_to_string(
            'account/email_validation.html',
            {
                'user': temp_user,
                'key': Validation.objects.create(user=temp_user).key,
                'base_domain': f'https://{settings.ALLOWED_HOSTS[0]}'
            }
        )
        send_mail(
            'فعال سازی حساب',
            strip_tags(email_template),
            settings.EMAIL_HOST_USER,
            (temp_user.email,),
            html_message=email_template
        )
        remove_user(temp_user.username)
        return redirect(self.success_url)


class Invites(LoginrequiredMixin, ListView):
    template_name = 'account/invites.html'
    paginate_by = 15

    def get_queryset(self):
        all_invites = UserInvite.objects.filter(user=self.request.user)
        if self.request.GET.get('status') and \
            status_filters := get_filters(self.requesr.GET['status'], UserInvite.Status):
                all_invites = all_invites.filter(status__in=status_filters)
        return all_invites


class MemberShips(LoginRequiredMixin, ListView):
    template_name = 'account/memberships.html'
    paginate_by = 15

    def get_queryset(self):
        memberships = Member.objects.filter(user=self.request.user)
        if keyword := self.request.GET.get('q'):
            memberships = memberships.filter(
                Q(group__name__icontains=keyword) |
                Q(group__description__icontains=keyword)
            )
        if self.request.GET.get('status') and \
            status_filters := get_filters(self.request.GET['status'], Member.Status):
                memberships = memberships.filter(status__in=status_filters)
        if self.request.GET.get('rank') and \
            rank_filters := get_filters(self.request.GET['rank'], Member.Rank):
            memberships = memberships.filter(rank__in=rank_filters)
        return memberships


@not_logged_in
def register_complete(request):
    return render(request, 'account/register_complete.html')


def verify_email(request, key):
    user = get_object_or_404(models.Validation, key=key, user__is_active=False).user
    user.is_active = True
    user.save()
    return render(request, 'account/verify_email.html')


class ProfileView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = Profile
    template_name = 'account/profile.html'

    def get_object(self, queryset=None):
        return self.request.user


@login_required
def invite_actions(request, invite_id: int, action: str):
    try:
        action = UserInvite.Status(action)
    except ValueError:
        return HttpresponseBadRequest('This action does not exist !')
    invite = get_object_or_404(UserInvite, id=invite_id, status=UserInvite.Status.pending)
    invite.status = action
    invite.save()
    return redirect('account:invites')
