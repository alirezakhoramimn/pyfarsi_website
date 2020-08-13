from django.http import HttpRequest
from blog.models import Article
from django.db.models import TextChoices


def check_author_or_superuser(request: HttpRequest, obj: Article):
    return request.user.is_superuser or not obj or obj.author == request.user


def get_filters(filters: str, choices: TextChoices, /):
    all_filters = filters.split(', ')
    return all_filters if all(target_filter in choices.values for target_filter in all_filters) else None
