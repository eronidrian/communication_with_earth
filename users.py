from constants import MAX_MESSAGES_IN_DISPATCH
from data_structures import User

USERS = {
    "no_account": User("No account", 0, False, 0),
    "earth": User("Earth", 1, False, MAX_MESSAGES_IN_DISPATCH),
    "test_encrypted_user": User("Test encrypted user", 7573188, True, 1),
    "test_unencrypted_user": User("Test unencrypted user", 3, False, 2)
}

def get_user_by_id(user_id: int) -> User | None:
    for user in USERS:
        if USERS[user].user_id == user_id:
            return USERS[user]
    return None
