import pickle
import logging
import socket
from abc import abstractmethod

from textual.app import App, ComposeResult
from textual import on
from textual_countdown import Countdown

from constants import SECONDS_BETWEEN_DISPATCHES, SERVER_IP, SERVER_PORT, SECONDS_BETWEEN_CONNECTION_CHECKS
from data_structures import TextMessage, Dispatch
from user_interface import TimeDisplay, DispatchDisplay, TextMessageInput, MainDisplay

def is_socket_closed(sock: socket.socket) -> bool:
    try:
        # this will try to read bytes without blocking and also without removing them from buffer (peek only)
        data = sock.recv(16, socket.MSG_DONTWAIT | socket.MSG_PEEK)
        if len(data) == 0:
            return True
    except BlockingIOError:
        return False  # socket is open and reading from it would block
    except ConnectionResetError:
        return True  # socket was closed for some other reason
    except Exception:
        return False
    return False

class BaseApp(App):
    CSS_PATH = "stylesheet.tcss"
    BINDINGS = [("w,W", "write_message", "Write message")] #("ctrl+c", "do_nothing")]
    ENABLE_COMMAND_PALETTE = False

    TITLE = "System for communication with the Earth"


    def __init__(self):
        self.connection_check_timer = None
        self.host = SERVER_IP
        self.port = SERVER_PORT
        self.logger = logging.getLogger()

        super().__init__()
    
    
    def on_mount(self):
        self.connection_check_timer = self.set_interval(SECONDS_BETWEEN_CONNECTION_CHECKS, self.check_connection)

    def can_be_message_added_to_dispatch(self, text_message: TextMessage) -> bool:
        if self.query_one(MainDisplay).get_last_dispatch_display().dispatch.is_full:
            self.notify(title="Full dispatch", message="The dispatch is full. Wait for the next dispatch.",
                        severity="error", timeout=5.0)
            self.logger.warning(f"User tried to add message to dispatch but reached dispatch limit.\n"
                             f"Message: {text_message}")
            return False
        return True

    @abstractmethod
    def create_text_message(self, text_message: TextMessageInput.TextMessageSubmitted) -> TextMessage:
        pass

    @on(TextMessageInput.TextMessageSubmitted)
    def add_text_message_to_dispatch_display(self, text_message: TextMessageInput.TextMessageSubmitted) -> None:
        new_text_message = self.create_text_message(text_message)

        if self.can_be_message_added_to_dispatch(new_text_message):
            self.query_one(MainDisplay).get_last_dispatch_display().add_new_text_message(new_text_message)
            self.notify(title="Message added", message="Message was successfully added to the dispatch", severity="information", timeout=5.0)
            self.logger.info(f"Message was successfully added to dispatch.\n"
                             f"Message: {new_text_message}")
        self.query(".text_message_input").first().remove()

    def check_connection(self):
        if is_socket_closed(self.peer):
            self.logger.error(f"Connection was lost.")
            self.notify(title="Connection lost", message="Connection was lost. Inform administrator about the problem.", severity="error", timeout=10.0 )
   

    def send_dispatch(self, dispatch_to_send: Dispatch) -> None:
        try:
            self.peer.sendall(pickle.dumps(dispatch_to_send))
        except BaseException as error:
            self.notify(title="Connection error",
                        message="The dispatch cannot be sent due to connection error. Inform administrator about the problem",
                        severity="error", timeout=30.0)
            self.logger.error(f"Dispatch couldn't be sent because of the following error: {error}")
            return
        self.notify(message="The dispatch has been successfully sent.", severity="information", timeout=5.0)
        self.logger.info("Dispatch has been successfully sent.\n"
                         f"Dispatch: {dispatch_to_send}")


    def show_received_dispatch(self, received_dispatch):
        received_dispatch_display = self.create_dispatch_display(received_dispatch, received=True)
        self.query_one(MainDisplay).add_dispatch_display(received_dispatch_display)
        self.notify(title="New dispatch", message="You have received a new dispatch.", severity="information", timeout=5.0)

    def handle_encryption(self, received_dispatch: Dispatch) -> None:
        pass

    def receive_dispatch(self) -> None:
        received_data = self.peer.recv(16384)
        if not received_data:
            self.notify(title="Connection error",
                        message="The dispatch cannot be received due to connection error. Inform administrator about the problem",
                        severity="error", timeout=30.0)
            self.logger.error(f"Dispatch was not received. Received no data")
            return

        received_dispatch = pickle.loads(received_data)
        self.logger.info(f"New dispatch was received.\n"
                         f"Dispatch: {received_dispatch}")
        self.action_bell()

        self.handle_encryption(received_dispatch)

        self.show_received_dispatch(received_dispatch)

    def create_dispatch_display(self, dispatch: Dispatch, received: bool) -> DispatchDisplay:
        return DispatchDisplay(dispatch, received=received)


    @on(TimeDisplay.TimeToSendDispatch)
    def handle_incoming_and_outgoing_dispatch(self) -> None:
        dispatch_to_send = self.query_one(MainDisplay).get_last_dispatch_display().dispatch
        self.send_dispatch(dispatch_to_send)

        self.receive_dispatch()

        new_dispatch_display = self.create_dispatch_display(Dispatch(), received=False)
        self.query_one(MainDisplay).add_dispatch_display(new_dispatch_display)

        self.query_one(Countdown).cancel()
        self.query_one(Countdown).start(SECONDS_BETWEEN_DISPATCHES)

    def action_write_message(self) -> None:
        message_input_widget = TextMessageInput(classes="text_message_input")
        self.mount(message_input_widget)
        message_input_widget.scroll_visible()

    @abstractmethod
    def compose(self) -> ComposeResult:
        pass
