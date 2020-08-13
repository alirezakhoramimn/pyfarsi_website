from django.urls import path
from . import views
app_name = 'snippets'
urlpatterns = (
    path('group/<int:pk>/<slug:slug>/', views.Group.as_view(), name='group'),
    path('create-group/', views.CreateGroup.as_view(), name='create_group'),
    path('join-group-with-link/<str:invite_id>/', views.join_group, name='join_group_with_link'),
    path('create-snippet/<int:group_id>/', views.CreateSnippet.as_view(), name='create_snippet'),
    path('snippet/<int:pk>/', views.Snippet.as_view(), name='snippet'),
    path('join-group/<int:group_id>/', views.join_group, name='join_group'),
    path('take-actions/<int:object_id>/<str:object_type>/<str:action>/', views.take_actions, name='snippet_actions'),
    path('snippets/<int:page>/', views.Snippets.as_view(), name='snippets'),
    path('get-groups/<str:q>/', views.GetGroups.as_view(), name='get_groups'),
    path('groups/<int:page>/', views.Groups.as_view(), name='groups'),
    path('telegram-groups/<int:group_id>/<int:page>/', views.TelegramGroups.as_view(), name='telegram_groups'),
    path('create-telegram-group/<int:group_id>/', views.CreateTelegramGroup.as_view(), name='create_telegram_group'),
    path('telegram-group/<int:pk>/', views.TelegramGroup.as_view(), name='telegram_group'),
    path('delete-telegram-group/<int:pk>/', views.DeleteTelegramGroup.as_view(), name='delete_telegram_group'),
    path('get-users/', views.GetUsers.as_view(), name='get_users'),
    path('create-user-invites/<int:group_id>/', views.CreateUserInvites.as_view(), name='create_user_invites'),
    path('members/<int:group_id>/<int:page>/', views.Members.as_view(), name='members'),
    path('member/<int:pk>/', views.Member.as_view(), name='member')
)
