from constants import MAX_MESSAGES_IN_DISPATCH
from data_structures import User

USERS = {
    "no_account": User("No account", 0, False, 0),
    "earth": User("Země", 1, False, MAX_MESSAGES_IN_DISPATCH),
    "olga_kovalenko": User("Olga Kovalenko", 6973377, True, 2),
    "senators": User("Senátoři", 6989607, False, 2),
    "mica_creeve": User("Mica Creeve", 7573188, False, 4),
    "tim_coreway": User("Tim Coreway", 7067089, False, 1),
    "philip_grigore": User("Philip Grigore", 8200492, True, 2),
    "sin_le_pham": User("Sin Le Pham", 8228611, False, 1)
}

def get_user_by_id(user_id: int) -> User | None:
    for user in USERS:
        if USERS[user].user_id == user_id:
            return USERS[user]
    return None
