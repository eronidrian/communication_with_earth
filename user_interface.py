import pickle
import os

from textual import events
from textual.app import ComposeResult
from textual.containers import ScrollableContainer, Horizontal, Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static, Input, Label, Button, Rule

from constants import SECONDS_BETWEEN_DISPATCHES, MESSAGE_MAX_LENGTH, SUBJECT_MAX_LENGTH, BACKUP_FILE
from data_structures import TextMessage, Dispatch, User
from users import USERS


class UserInfoDisplay(Static):
    """Show info about the current user"""

    user = reactive(USERS["no_account"])
    def render(self):
        if self.user == USERS["no_account"]:
            return "Current user ID: 0 (nobody logged in)"
        else:
            return (f"Current user ID: {self.user.user_id}\n"
                    f"Text message limit: {self.user.text_message_limit}")


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


class TextMessageDisplay(Static):
    """Display single message"""

    COMPONENT_CLASSES = {
        "text_message_display"
    }

    def __init__(self, text_message: TextMessage) -> None:
        self.text_message = text_message
        super().__init__()

    def display_user(self, user: User):
        return f"{user.user_id}"

    def compose(self) -> ComposeResult:
        with Horizontal(classes="message_header"):
            with Vertical():
                yield Static(f"Sender: {self.display_user(self.text_message.sender)}")
                yield Static(f"Recipient: {self.display_user(self.text_message.recipient)}")
                yield Static(f"Subject: {self.text_message.subject}\n")
            yield Static(f"{self.text_message.time_added}", classes="message_time")
        yield Rule()
        yield Static(self.text_message.text)


class DispatchDisplay(Static):
    """Display whole dispatch"""

    COMPONENT_CLASSES = {
        "dispatch_display"
    }

    text_message_display_class = TextMessageDisplay

    def __init__(self, dispatch: Dispatch, received: bool) -> None:
        self.dispatch = dispatch
        self.is_received = received
        super().__init__()

        if received:
            self.add_class("received")
        else:
            self.add_class("sent")

    def add_new_text_message(self, text_message: TextMessage) -> bool:
        if self.dispatch.add_new_text_messages(text_message):
            text_message_display = self.text_message_display_class(text_message)
            self.mount(text_message_display)
            text_message_display.scroll_visible()
            return True
        else:
            return False

    def compose(self) -> ComposeResult:
        for text_message in self.dispatch.text_messages:
            yield self.text_message_display_class(text_message)


class MainDisplay(ScrollableContainer):
    """Main display for dispatches"""

    COMPONENT_CLASSES = {
        "main_display"
    }

    dispatch_display_class = DispatchDisplay

    def __init__(self) -> None:
        self.dispatch_displays: list[DispatchDisplay] = []
        super().__init__()

    def on_mount(self, event: events.Mount) -> None:
        self.restore_from_backup()
        self.add_dispatch_display(self.dispatch_display_class(Dispatch(), received=False))

    def get_last_dispatch_display(self) -> DispatchDisplay:
        return self.dispatch_displays[-1]

    def create_dispatch_display(self, dispatch: Dispatch, received: bool) -> DispatchDisplay:
        return self.dispatch_display_class(dispatch, received)

    def add_dispatch_display(self, dispatch_display: DispatchDisplay) -> None:
        self.dispatch_displays.append(dispatch_display)
        self.mount(dispatch_display)
        dispatch_display.scroll_visible()
        self.backup()

    def backup(self):
        dispatches = []
        for dispatch_display in self.dispatch_displays:
            if not dispatch_display.dispatch.text_messages:
                continue
            dispatches.append((dispatch_display.dispatch, dispatch_display.is_received))
        if dispatches:
            with open(BACKUP_FILE, "wb") as backup:
                pickle.dump(dispatches, backup)

    def restore_from_backup(self):
        if os.stat(BACKUP_FILE).st_size < 50:
            return
        with open(BACKUP_FILE, "rb") as backup:
            dispatches = pickle.load(backup)
        for dispatch in dispatches:
            if not dispatch[0].text_messages:
                continue
            dispatch_display = self.create_dispatch_display(dispatch[0], dispatch[1])
            self.add_dispatch_display(dispatch_display)

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
        subject_len = len(self.query_one("#subject").value)
        if subject_len > SUBJECT_MAX_LENGTH:
            self.notify(title="Subject too long",
                        message=f"The message subject is {subject_len} long. Maximum length is {SUBJECT_MAX_LENGTH} characters.",
                        severity="error", timeout=5.0)
            return False
        text_len = len(self.query_one("#text").value)
        if text_len > MESSAGE_MAX_LENGTH:
            self.notify(title="Text too long",
                        message=f"The message text is {text_len} long. Maximum length is {MESSAGE_MAX_LENGTH} characters.",
                        severity="error", timeout=5.0)
            return False
        return True

    def send_button_pressed(self) -> None:
        if not self.validate_text_message():
            return

        subject = self.query_one("#subject").value
        text = self.query_one("#text").value

        self.post_message(self.TextMessageSubmitted(None, None, subject, text))

    def cancel_button_pressed(self) -> None:
        self.remove()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "send":
            self.send_button_pressed()
        elif event.button.id == "cancel":
            self.cancel_button_pressed()

        event.prevent_default()

    def on_input_submitted(self, message: Input.Submitted) -> None:
        if message.input.id == "subject":
            self.query_one("#text").focus()
        if message.input.id == "text":
            self.send_button_pressed()

    def compose(self) -> ComposeResult:
        yield Label("Subject:")
        yield Input(id="subject", placeholder="Specify message recipient or subject")
        yield Label("Text:")
        yield Input(id="text", placeholder="Write message text")
        with Horizontal():
            yield Button(label="Send", variant="success", id="send")
            yield Button(label="Cancel", variant="error", id="cancel")
