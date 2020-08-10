from .models import Snippet, Member
from . import types


def take_action(target_object, action: actions.Actions):
    if action is not types.Actions.DELETE:
        if action is types.Actions.CLOSE_SNIPPET:
            target_object.status = Snippet.Status.closed
        else:
            target_object.status = Member.Status.member
        target_object.save()
    else:
        target_object.delete()
