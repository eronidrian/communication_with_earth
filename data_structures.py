import base64

from constants import MAX_MESSAGES_IN_DISPATCH

class User:
    def __init__(self, name: str, user_id: int, encryption_on: bool, text_message_limit: int) -> None:
        self.name = name
        self.user_id = user_id
        self.encryption_on = encryption_on
        self.text_message_limit = text_message_limit

    def __str__(self):
        return f"{self.name} ({self.user_id})"

class TextMessage:
    encrypted = False

    def __init__(self, sender: User, recipient: User, subject: str, text: str, time_added: str) -> None:
        self.time_added = time_added
        self.sender = sender
        self.recipient = recipient
        self.subject = subject
        self.text = text

    def encrypt(self) -> None:
        self.text = base64.b64encode(self.text.encode()).decode()
        self.encrypted = True

    def decrypt(self) -> None:
        self.text = base64.b64decode(self.text).decode()
        self.encrypted = False

    def __str__(self):
        return (f"Time added: {self.time_added}\n"
                f"Sender: {self.sender}\n"
                f"Recipient: {self.recipient}\n"
                f"Subject: {self.subject}\n"
                f"Text: {self.text}\n")


class Dispatch:
    max_text_messages = MAX_MESSAGES_IN_DISPATCH

    def __init__(self, *text_messages) -> None:
        self.text_messages = []
        for text_message in text_messages:
            self.text_messages.append(text_message)

    def add_new_text_messages(self, *text_messages: TextMessage) -> bool:
        if len(text_messages) > self.max_text_messages or len(text_messages) + len(
                self.text_messages) > self.max_text_messages:
            return False
        for text_message in text_messages:
            self.text_messages.append(text_message)
        return True

    def get_all_text_messages(self) -> list[TextMessage]:
        return self.text_messages

    def is_full(self):
        return len(self.text_messages) == self.max_text_messages

    def encrypt_all_messages(self) -> None:
        for text_message in self.text_messages:
            if text_message.encrypted:
                continue
            if text_message.recipient.encryption_on or text_message.sender.encryption_on:
                text_message.encrypt()

    def encrypt_all_messages_of_user(self, user: User) -> None:
        for text_message in self.text_messages:
            if text_message.encrypted:
                continue
            if text_message.sender.user_id == user.user_id or text_message.recipient.user_id == user.user_id:
                text_message.encrypt()

    def decrypt_all_messages(self) -> None:
        for text_message in self.text_messages:
            if not text_message.encrypted:
                continue
            text_message.decrypt()

    def decrypt_all_messages_of_user(self, user: User) -> None:
        for text_message in self.text_messages:
            if not text_message.encrypted:
                continue
            if text_message.sender.user_id == user.user_id or text_message.recipient.user_id == user.user_id:
                text_message.decrypt()

    def count_messages_by_sender(self, sender: User):
        count = 0
        for text_message in self.text_messages:
            if text_message.sender.user_id == sender.user_id:
                count += 1

        return count

    def __str__(self):
        result = ""
        for text_message in self.text_messages:
            result += f"{text_message}\n"

        return result

KEY_MAPPINGS = {
    "+" : "1",
    "ě" : "2",
    "š" : "3",
    "č" : "4",
    "ř" : "5",
    "ž" : "6",
    "ý" : "7",
    "á" : "8",
    "í" : "9",
    "é" : "0"
}

def decode_card_id(number: str) -> int:
    new_number = ""
    for letter in number:
        new_number += KEY_MAPPINGS[letter]

    return int(new_number)