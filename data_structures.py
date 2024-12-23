import base64
import textwrap

from constants import MAX_MESSAGES_IN_DISPATCH


class User:
    def __init__(self, name: str, user_id: int, encryption_on: bool, text_message_limit: int) -> None:
        self.name = name
        self.user_id = user_id
        self.encryption_on = encryption_on
        self.text_message_limit = text_message_limit

    def __str__(self):
        return f"{self.name} ({self.user_id})"

    def __eq__(self, other):
        return self.user_id == other.user_id


class TextMessage:

    def __init__(self, sender: User, recipient: User, subject: str, text: str, time_added: str) -> None:
        self.time_added = time_added
        self.sender = sender
        self.recipient = recipient
        self.subject = subject
        self.text = text
        self.is_encrypted = False

    def encrypt(self) -> None:
        if self.is_encrypted:
            return None
        self.text = base64.b64encode(self.text.encode()).decode()
        self.is_encrypted = True

    def decrypt(self) -> None:
        if not self.is_encrypted:
            return None
        self.text = base64.b64decode(self.text).decode()
        self.is_encrypted = False

    def pretty_print(self) -> str:
        message = (f"-" * 70 + f"\n" +
                   f"Header\n" +
                   f"-" * 70 + f"\n" +
                   f"Time added: {self.time_added}\n" +
                   f"Sender: {self.sender.user_id}\n" +
                   f"Recipient: {self.recipient.user_id}\n" +
                   f"Subject: {self.subject}\n" +
                   f"-" * 70 + f"\n" +
                   f"Body\n" +
                   f"-" * 70 + f"\n")
        message += '\n'.join(textwrap.wrap(self.text, 70))
        return message + '\n'

    def __str__(self):
        return (f"Time added: {self.time_added}\n"
                f"Sender: {self.sender}\n"
                f"Recipient: {self.recipient}\n"
                f"Subject: {self.subject}\n"
                f"Text: {self.text}\n")


class Dispatch:
    max_text_messages = MAX_MESSAGES_IN_DISPATCH

    def __init__(self, *text_messages: TextMessage) -> None:
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

    @property
    def is_full(self):
        return len(self.text_messages) == self.max_text_messages

    @property
    def is_empty(self):
        return len(self.text_messages) == 0

    def encrypt_all_messages(self) -> None:
        for text_message in self.text_messages:
            if text_message.recipient.encryption_on or text_message.sender.encryption_on:
                text_message.encrypt()

    def encrypt_all_messages_of_user(self, user: User) -> None:
        for text_message in self.text_messages:
            if text_message.sender == user or text_message.recipient == user:
                text_message.encrypt()

    def decrypt_all_messages(self) -> None:
        for text_message in self.text_messages:
            text_message.decrypt()

    def decrypt_all_messages_of_user(self, user: User) -> None:
        for text_message in self.text_messages:
            if text_message.sender == user or text_message.recipient == user:
                text_message.decrypt()

    def count_messages_by_sender(self, sender: User):
        count = 0
        for text_message in self.text_messages:
            if text_message.sender == sender:
                count += 1

        return count

    def pretty_print(self) -> str:
        result = ""
        for text_message in self.text_messages:
            result += (f"{text_message.pretty_print()}\n" +
                       f"=" * 70 + f"\n")
        return result

    def __str__(self):
        result = ""
        for text_message in self.text_messages:
            result += f"{text_message}\n"

        return result


KEY_MAPPINGS = {
    "+": "1",
    "ě": "2",
    "š": "3",
    "č": "4",
    "ř": "5",
    "ž": "6",
    "ý": "7",
    "á": "8",
    "í": "9",
    "é": "0"
}


def decode_card_id(number: str) -> int:
    new_number = ""
    for letter in number:
        new_number += KEY_MAPPINGS[letter]

    return int(new_number)
