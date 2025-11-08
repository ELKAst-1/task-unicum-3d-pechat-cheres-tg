from enum import Enum

class UserStates(Enum):
    FIRST_NAME = 1
    LAST_NAME = 2
    GROUP = 3
    PURPOSE = 4
    FILE = 5

class AdminStates(Enum):
    VIEW_REQUESTS = 1
    MANAGE_GROUPS = 2
    MANAGE_PURPOSES = 3
    ADDING_GROUP = 4
    ADDING_PURPOSE = 5
    ADDING_COMMENT = 6
    MESSAGING_USER = 7
