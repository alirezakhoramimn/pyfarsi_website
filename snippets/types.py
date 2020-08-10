from enum import Enum


class Actions(Enum):
    DELETE = 'delete'
    CLOSE_SNIPPET = 'close_snippet'
    ACCEPT_MEMBER = 'accept_member'


class Types(Enum):
    SNIPPET = 'snippet'
    MEMBER = 'member'
