import socket
import pickle
import logging
from itertools import filterfalse

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer
from textual import on
from textual_countdown import Countdown

from app import CommunicationDevice
from constants import SECONDS_BETWEEN_DISPATCHES
from data_structures import User, TextMessage, Dispatch
from users import USERS
from user_interface import UserInfoDisplay, TimeDisplay, DispatchDisplay, MainDisplay, TextMessageInput


class ClientMainDisplay(MainDisplay):

    def encrypt_all_dispatches_of_user(self, user: User) -> None:
        for dispatch_display in self.dispatch_displays:
            dispatch_display.dispatch.encrypt_all_messages_of_user(user)

    def decrypt_all_dispatches_of_user(self, user: User) -> None:
        for dispatch_display in self.dispatch_displays:
            dispatch_display.dispatch.decrypt_all_messages_of_user(user)


class Client(CommunicationDevice):

    BINDINGS = [("i", "log_in", "Log in"), ("o", "log_out", "Log out"), ("w", "write_message", "Write message")]

    peer = socket.socket()

    def __init__(self):
        super().__init__()
        self.current_user = USERS["no_account"]

    def on_mount(self):
        logging.basicConfig(filename="client.log", encoding="utf-8", level=logging.DEBUG,
                            format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
        self.logger.info("Client started")

        self.peer.connect((self.host, self.port))
        self.logger.debug(f"Connected to server on {self.host} on port {self.port}")

        self.query_one(Countdown).start(SECONDS_BETWEEN_DISPATCHES)

    def can_be_message_added_to_dispatch(self, text_message: TextMessage) -> bool:
        if self.query_one(ClientMainDisplay).get_last_dispatch_display().get_dispatch().count_messages_by_sender(
                self.current_user) == self.current_user.text_message_limit:
            self.notify(
                message="You have reached the limit of messages available for your account. Wait for the next dispatch.",
                severity="error", timeout=5.0)
            self.query_one(TextMessageInput).remove()
            self.logger.warning(f"User tried to add message to dispatch but reached his message limit.\n"
                                f"Message: {text_message}")
            return False
        return super().can_be_message_added_to_dispatch(text_message)

    def action_log_in(self) -> None:
        # TODO: handle identification cards
        self.notify(title="Provide identification", message=f"Place your identification card on the reader",
                    severity="information", timeout=5.0)
        self.current_user = USERS["test_encrypted_user"]
        if self.current_user.encryption_on:
            self.query_one(ClientMainDisplay).decrypt_all_dispatches_of_user(self.current_user)
            self.query_one(ClientMainDisplay).refresh(recompose=True)
        self.query_one(UserInfoDisplay).update(f"{self.current_user.user_id} is logged in")
        self.notify(title=f"Welcome", message=f"You successfully logged in as {self.current_user.user_id}",
                    severity="information",
                    timeout=5.0)
        self.logger.info(f"User {self.current_user} logged in")

    def action_log_out(self) -> None:
        self.refresh_bindings()
        if self.current_user.encryption_on:
            self.query_one(ClientMainDisplay).encrypt_all_dispatches_of_user(self.current_user)
            self.query_one(ClientMainDisplay).refresh(recompose=True)
        past_user = self.current_user
        self.current_user = USERS["no_account"]
        self.query_one(UserInfoDisplay).update(f"User ID: {self.current_user.user_id} (nobody logged in)")
        self.notify(title="Goodbye", message="You successfully logged out", severity="information", timeout=5.0)
        self.logger.info(f"User {past_user} logged out")

    def action_write_message(self) -> None:
        if self.current_user.user_id == 0:
            self.notify(message="You are not logged in. Log in to write messages.", severity="error", timeout=5.0)
            self.logger.warning("Somebody tried to write message without logging in")
        else:
            super().action_write_message()

    def encrypt_received_dispatch(self, received_dispatch: Dispatch) -> None:
        received_dispatch.encrypt_all_messages()
        if self.current_user.encryption_on:
            received_dispatch.decrypt_all_messages_of_user(self.current_user)

    def create_text_message(self, text_message: TextMessageInput.TextMessageSubmitted) -> TextMessage:
        return TextMessage(self.current_user, USERS["earth"], text_message.subject, text_message.text)

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Footer()
        yield UserInfoDisplay(f"User ID: {self.current_user.user_id} (nobody logged in)")
        yield TimeDisplay()
        yield Countdown()
        yield ClientMainDisplay()


if __name__ == "__main__":
    app = Client()
    app.run()
