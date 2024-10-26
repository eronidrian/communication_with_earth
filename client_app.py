import socket
import logging
from datetime import datetime

from textual import events
from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widgets import Header, Footer
from textual_countdown import Countdown

from app import BaseApp
from constants import SECONDS_BETWEEN_DISPATCHES, CLIENT_LOG
from data_structures import User, TextMessage, Dispatch, decode_card_id, KEY_MAPPINGS
from users import USERS, get_user_by_id
from user_interface import UserInfoDisplay, TimeDisplay, MainDisplay, TextMessageInput


class ClientMainDisplay(MainDisplay):

    def encrypt_all_dispatches_of_user(self, user: User) -> None:
        for dispatch_display in self.dispatch_displays:
            dispatch_display.dispatch.encrypt_all_messages_of_user(user)

    def decrypt_all_dispatches_of_user(self, user: User) -> None:
        for dispatch_display in self.dispatch_displays:
            dispatch_display.dispatch.decrypt_all_messages_of_user(user)


class ClientApp(BaseApp):
    BINDINGS = [("i", "log_in", "Log in"), ("o", "log_out", "Log out"), ("w", "write_message", "Write message")]

    peer = socket.socket()

    submitted_id = reactive("")

    def __init__(self):
        super().__init__()
        self.current_user = USERS["no_account"]
        self.submitting_id = False

    def on_mount(self):
        logging.basicConfig(filename=CLIENT_LOG, encoding="utf-8", level=logging.DEBUG,
                            format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
        self.logger.info("Client started")

        self.peer.connect((self.host, self.port))
        self.logger.debug(f"Connected to server on {self.host} on port {self.port}")

        self.query_one(Countdown).start(SECONDS_BETWEEN_DISPATCHES)

    def can_be_message_added_to_dispatch(self, text_message: TextMessage) -> bool:
        if self.query_one(ClientMainDisplay).get_last_dispatch_display().dispatch.count_messages_by_sender(
                self.current_user) == self.current_user.text_message_limit:
            self.notify(
                title="Message limit reached",
                message=f"You cannot add more messages to this dispatch. Your limit is "
                        f"{self.current_user.text_message_limit} messages. Wait for the next dispatch.",
                severity="error", timeout=5.0)
            self.query_one(TextMessageInput).remove()
            self.logger.warning(f"User tried to add message to dispatch but reached his message limit.\n"
                                f"Message: {text_message}")
            return False
        return super().can_be_message_added_to_dispatch(text_message)

    def on_key(self, event: events.Key) -> None:
        if len(self.submitted_id) < 10 and event.character in KEY_MAPPINGS.keys() and self.submitting_id:
            self.submitted_id += event.character
        if event.character not in KEY_MAPPINGS.keys():
            self.submitting_id = False

    def watch_submitted_id(self, submitted_id: str) -> None:
        if len(submitted_id) == 10:
            self.handle_login()

    def handle_login(self):
        parsed_id = decode_card_id(self.submitted_id)
        self.logger.info(f"Parsed_id: {parsed_id}")
        self.submitted_id = ""
        user = get_user_by_id(parsed_id)
        if user is None:
            self.logger.info(f"Somebody tried to login with ID {parsed_id}")
            self.notify(title="Invalid card", message="Your card is invalid. Inform administrator if the issue persists.", severity="error",
                        timeout=10.0)
            return
        self.current_user = user
        if self.current_user.encryption_on:
            self.query_one(ClientMainDisplay).decrypt_all_dispatches_of_user(self.current_user)
            self.query_one(ClientMainDisplay).refresh(recompose=True)
        self.query_one(UserInfoDisplay).update(f"{self.current_user.user_id} is logged in")
        self.notify(title=f"Welcome", message=f"You successfully logged in as {self.current_user.user_id}",
                    severity="information",
                    timeout=5.0)
        self.logger.info(f"User {self.current_user} logged in")

    def action_log_in(self) -> None:
        self.notify(title="Provide identification", message=f"Place your identification card on the reader",
                    severity="information", timeout=5.0)
        self.submitted_id = ""
        self.submitting_id = True

    def action_log_out(self) -> None:
        self.refresh_bindings()
        # TODO: hide bindings
        if self.current_user == USERS["no_account"]:
            self.notify(title="Nobody logged in", message="You cannot log out. Nobody is logged in", severity="error",
                        timeout=5.0)
            return
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
            self.notify(title="Invalid permission", message="You are not logged in. Log in to write messages.", severity="error", timeout=5.0)
            self.logger.warning("Somebody tried to write message without logging in")
        else:
            super().action_write_message()

    def handle_encryption(self, received_dispatch: Dispatch) -> None:
        received_dispatch.encrypt_all_messages()
        if self.current_user.encryption_on:
            received_dispatch.decrypt_all_messages_of_user(self.current_user)

    def create_text_message(self, text_message: TextMessageInput.TextMessageSubmitted) -> TextMessage:
        return TextMessage(self.current_user, USERS["earth"], text_message.subject, text_message.text,
                           datetime.now().strftime("%H:%M:%S"))

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Footer()
        yield UserInfoDisplay(f"User ID: {self.current_user.user_id} (nobody logged in)")
        yield TimeDisplay()
        yield Countdown()
        yield ClientMainDisplay()


if __name__ == "__main__":
    app = ClientApp()
    app.run()
