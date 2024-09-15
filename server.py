import socket
import pickle
import logging

from textual import on
from textual.app import ComposeResult, App
from textual.widgets import Static, Header, Footer, Select, Label, Input, Button
from textual_countdown import Countdown

from app import CommunicationDevice
from constants import SECONDS_BETWEEN_DISPATCHES
from data_structures import TextMessage, Dispatch
from users import USERS
from user_interface import TimeDisplay, TextMessageInput, DispatchDisplay, MainDisplay

class ServerDispatchDisplay(DispatchDisplay):

    class ServerTextMessageDisplay(DispatchDisplay.TextMessageDisplay):

        def compose(self) -> ComposeResult:
            yield Static(f"Sender: {self.text_message.sender.name} ({self.text_message.sender.user_id})")
            yield Static(f"Recipient: {self.text_message.recipient.name} ({self.text_message.recipient.user_id})")
            yield Static(f"Subject: {self.text_message.subject}\n")
            yield Static(self.text_message.text)

    def add_new_text_message(self, text_message: TextMessage) -> bool:
        if self.dispatch.add_new_text_messages(text_message):
            text_message_display = self.ServerTextMessageDisplay(text_message)
            self.mount(text_message_display)
            text_message_display.scroll_visible()
            return True
        else:
            return False

    def compose(self) -> ComposeResult:
        for text_message in self.dispatch.get_all_text_messages():
            yield self.ServerTextMessageDisplay(text_message)


class ServerMainDisplay(MainDisplay):


    COMPONENT_CLASSES = {
        "main_display"
    }

    def on_mount(self) -> None:
        if len(self.dispatch_displays) == 0:
            self.add_dispatch_display(ServerDispatchDisplay(Dispatch(), received=False))


class ServerTextMessageInput(TextMessageInput):
    """Input text messages server side"""

    def server_validate_text_message(self):
        if self.query_one("#recipient").is_blank():
            self.notify(title="No recipient",
                        message="The message does not have any recipient. Select the recipient", severity="error",
                        timeout=5.0)
            return False

        return super().validate_text_message()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if not self.server_validate_text_message():
            return

        subject = self.query_one("#subject").value
        text = self.query_one("#text").value
        recipient = self.query_one("#recipient").value

        self.post_message(self.TextMessageSubmitted(None, recipient, subject, text))

        event.prevent_default()

    def on_input_submitted(self, message: Input.Submitted) -> None:
        if message.input.id == "subject":
            self.query_one("#text").focus()
        if message.input.id == "text":
            self.query_one("#recipient").focus()

    def compose(self) -> ComposeResult:
        yield Label("Subject:")
        yield Input(id="subject")
        yield Label("Text:")
        yield Input(id="text")
        yield Label("Recipient:")
        yield Select(id="recipient", options=[(USERS[user].name, user) for user in USERS])
        yield Button(label="Send", variant="success")


class Server(CommunicationDevice):

    peer = None
    client = None
    address = None
    s = None


    def on_mount(self):
        logging.basicConfig(filename="server.log", encoding="utf-8", level=logging.DEBUG,
                            format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
        self.logger.info("Server started")

        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.bind(("192.168.0.45", self.port))
        self.logger.info(f"Socket is bound to {self.host} on port {self.port}")

        self.s.listen(5)
        self.peer, self.address = self.s.accept()
        self.logger.info(f"Client connected from address {self.address}")

        self.query_one(Countdown).start(SECONDS_BETWEEN_DISPATCHES)


    def create_text_message(self, text_message: TextMessageInput.TextMessageSubmitted) -> TextMessage:
        return TextMessage(USERS["earth"], USERS[text_message.recipient], text_message.subject,
                                       text_message.text)

    def action_write_message(self) -> None:
        message_input_widget = ServerTextMessageInput()
        self.mount(message_input_widget)
        message_input_widget.scroll_visible()

    def create_dispatch_display(self, dispatch: Dispatch, received: bool) -> DispatchDisplay:
        return ServerDispatchDisplay(dispatch, received=received)

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Footer()
        yield TimeDisplay()
        yield Countdown()
        yield ServerMainDisplay()


if __name__ == "__main__":
    app = Server()
    app.run()
