from textual.app import ComposeResult
from textual.containers import ScrollableContainer
from textual.message import Message
from textual.reactive import reactive
from textual.renderables.digits import Digits
from textual.widget import Widget
from textual.widgets import Static, Input, Label, Button

from constants import SECONDS_BETWEEN_DISPATCHES, MESSAGE_MAX_LENGTH, SUBJECT_MAX_LENGTH
from data_structures import TextMessage, Dispatch, User


class UserInfoDisplay(Static):
    """Show info about the current user"""


class TimeDisplay(Static):
    tick_timer = None

    seconds_between_dispatches = SECONDS_BETWEEN_DISPATCHES
    time_left = reactive(seconds_between_dispatches)

    class TimeToSendDispatch(Message):
        """Time until the next dispatch ran out"""

    def on_mount(self) -> None:
        self.tick_timer = self.set_interval(1, self.tick)

    def tick(self) -> None:
        self.time_left -= 1
        if self.time_left == -1:
            self.post_message(self.TimeToSendDispatch())
            self.reset()

    def watch_time_left(self, time_left: int) -> None:
        minutes, seconds = divmod(time_left, 60)
        hours, minutes = divmod(minutes, 60)
        self.update(f"Time before the current dispatch is sent: {hours:02,.0f}:{minutes:02.0f}:{seconds:02.0f}")

    def reset(self):
        self.time_left = self.seconds_between_dispatches


class DispatchDisplay(Static):
    """Display whole dispatch"""

    COMPONENT_CLASSES = {
        "dispatch_display"
    }

    class TextMessageDisplay(Static):
        """Display single message"""

        COMPONENT_CLASSES = {
            "text_message_display"
        }

        def __init__(self, text_message: TextMessage) -> None:
            self.text_message = text_message
            super().__init__()

        def compose(self) -> ComposeResult:
            yield Static(f"Sender: {self.text_message.sender.user_id}")
            yield Static(f"Recipient: {self.text_message.recipient.user_id}")
            yield Static(f"Subject: {self.text_message.subject}\n")
            yield Static(self.text_message.text)

    def __init__(self, dispatch: Dispatch, received: bool) -> None:
        self.dispatch = dispatch
        super().__init__()

        if received:
            self.add_class("received")
        else:
            self.add_class("sent")

    def get_dispatch(self) -> Dispatch:
        return self.dispatch

    def add_new_text_message(self, text_message: TextMessage) -> bool:
        if self.dispatch.add_new_text_messages(text_message):
            text_message_display = self.TextMessageDisplay(text_message)
            self.mount(text_message_display)
            text_message_display.scroll_visible()
            return True
        else:
            return False

    def compose(self) -> ComposeResult:
        for text_message in self.dispatch.get_all_text_messages():
            yield self.TextMessageDisplay(text_message)


class MainDisplay(ScrollableContainer):
    """Main display for dispatches"""
    dispatch_displays = []

    COMPONENT_CLASSES = {
        "main_display"
    }

    def on_mount(self) -> None:
        if len(self.dispatch_displays) == 0:
            self.add_dispatch_display(DispatchDisplay(Dispatch(), received=False))

    def get_last_dispatch_display(self) -> DispatchDisplay:
        return self.dispatch_displays[-1]

    def add_dispatch_display(self, dispatch_display: DispatchDisplay) -> None:
        self.dispatch_displays.append(dispatch_display)
        self.mount(dispatch_display)
        dispatch_display.scroll_visible()

    def compose(self) -> ComposeResult:
        for dispatch_display in self.dispatch_displays:
            yield dispatch_display


class TextMessageInput(Widget):
    """Input for message"""
    BINDINGS = [("s", "enter_subject", "Enter subject"), ("t", "enter_text", "Enter text"), ("f", "send", "Send")]

    COMPONENT_CLASSES = {"text_message_input"}

    class TextMessageSubmitted(Message):
        """When the message is submitted"""

        def __init__(self, sender: User, recipient: User, subject: str, text: str) -> None:
            self.sender = sender
            self.recipient = recipient
            self.subject = subject
            self.text = text
            super().__init__()


    def on_mount(self) -> None:
        self.query_one("#subject").focus()

    def validate_text_message(self):
        if self.query_one("#subject").value == "":
            self.notify(title="Empty subject",
                        message="The subject of the message cannot be empty. Fill in the subject.", severity="error",
                        timeout=5.0)
            return False
        if self.query_one("#text").value == "":
            self.notify(title="Empty text", message="The text of the message cannot be empty. Add some text.",
                        severity="error", timeout=5.0)
            return False
        if len(self.query_one("#subject").value) > SUBJECT_MAX_LENGTH:
            self.notify(title="Subject too long",
                        message=f"The subject of the message is too long. Maximum length is {SUBJECT_MAX_LENGTH} characters.",
                        severity="error", timeout=5.0)
            return False
        if len(self.query_one("#text").value) > MESSAGE_MAX_LENGTH:
            self.notify(title="Text too long",
                        message=f"The text of the message is too long. Maximum length is {MESSAGE_MAX_LENGTH} characters.",
                        severity="error", timeout=5.0)
            return False
        return True

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if not self.validate_text_message():
            return

        subject = self.query_one("#subject").value
        text = self.query_one("#text").value

        self.post_message(self.TextMessageSubmitted(None, None, subject, text))

    def on_input_submitted(self, message: Input.Submitted) -> None:
        if message.input.id == "subject":
            self.query_one("#text").focus()
        if message.input.id == "text":
            self.query_one("#send").action_press()

    def compose(self) -> ComposeResult:
        yield Label("Subject:")
        yield Input(id="subject")
        yield Label("Text:")
        yield Input(id="text")
        yield Button(label="Send", variant="success", id="send")
