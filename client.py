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





# class CommunicationDevice(App):
#     CSS_PATH = "stylesheet.tcss"
#     BINDINGS = [("i", "log_in", "Log in"), ("w", "write_message", "Write message"), ("o", "log_out", "Log out")]
#     ENABLE_COMMAND_PALETTE = False
#
#     TITLE = "System for communication with the Earth"
#     current_user = USERS["no_account"]
#
#     server = socket.socket()
#     host = socket.gethostname()
#     port = 12345
#
#     logger = logging.getLogger()
#
#     def on_mount(self):
#         logging.basicConfig(filename="client.log", encoding="utf-8", level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
#         self.logger.info("Client started")
#
#         self.server.connect((self.host, self.port))
#         self.logger.debug(f"Server connected on {self.host} on port {self.port}")
#
#         self.query_one(Countdown).start(SECONDS_BETWEEN_DISPATCHES)
#
#     @on(TextMessageInput.TextMessageSubmitted)
#     def add_text_message_to_dispatch_display(self, text_message: TextMessageInput.TextMessageSubmitted) -> None:
#         new_text_message = TextMessage(self.current_user, USERS["earth"], text_message.subject, text_message.text)
#
#         if self.query_one(ClientMainDisplay).get_last_dispatch_display().get_dispatch().count_messages_by_sender(
#                 self.current_user) == self.current_user.text_message_limit:
#             self.notify(
#                 message="You have reached the limit of messages available for your account. Wait for the next dispatch.",
#                 severity="error", timeout=5.0)
#             self.query_one(TextMessageInput).remove()
#             self.logger.warning(f"User tried to add message to dispatch but reached his message limit.\n"
#                              f"Message: {new_text_message}")
#             return
#         if not self.query_one(ClientMainDisplay).get_last_dispatch_display().add_new_text_message(new_text_message):
#             self.notify(message="The dispatch is full. Wait for the next dispatch.", title="Full dispatch",
#                         severity="error", timeout=5.0)
#             self.logger.warning(f"User tried to add message to dispatch but reached dispatch limit.\n"
#                              f"Message: {new_text_message}")
#         else:
#             self.notify(message="Message was successfully added to the dispatch", severity="information", timeout=5.0)
#             self.logger.info(f"Message was successfully added to dispatch.\n"
#                              f"Message: {new_text_message}")
#         self.query_one(TextMessageInput).remove()
#
#     def send_dispatch(self, dispatch_to_send: Dispatch) -> None:
#         try:
#             self.server.sendall(pickle.dumps(dispatch_to_send))
#         except BaseException as error:
#             self.notify(title="Connection error",
#                         message="The dispatch cannot be sent due to connection error. Inform administrator about the problem",
#                         severity="error", timeout=30.0)
#             self.logger.error(f"Dispatch couldn't be sent because of the following error: {error}")
#             return
#         self.notify(message="The dispatch has been successfully sent.", severity="information", timeout=5.0)
#         self.logger.info("Dispatch has been successfully sent.\n"
#                          f"Dispatch: {dispatch_to_send}")
#
#     def receive_dispatch(self) -> None:
#         received_data = self.server.recv(16384)
#         if not received_data:
#             self.notify(title="Connection error",
#                         message="The dispatch cannot be received due to connection error. Inform administrator about the problem",
#                         severity="error", timeout=30.0)
#             self.logger.error(f"Dispatch was not received. Received no data")
#             return
#
#         received_dispatch = pickle.loads(received_data)
#         self.logger.info(f"New dispatch was received.\n"
#                          f"Dispatch: {received_dispatch}")
#
#         received_dispatch.encrypt_all_messages()
#         if self.current_user.encryption_on:
#             received_dispatch.decrypt_all_messages_of_user(self.current_user)
#
#         received_dispatch_display = DispatchDisplay(received_dispatch, received=True)
#         self.query_one(ClientMainDisplay).add_dispatch_display(received_dispatch_display)
#         self.notify(message="You have received a new dispatch.", severity="information", timeout=5.0)
#
#         return received_dispatch
#
#     @on(TimeDisplay.TimeToSendDispatch)
#     def handle_incoming_and_outgoing_dispatch(self) -> None:
#         dispatch_to_send = self.query_one(ClientMainDisplay).get_last_dispatch_display().get_dispatch()
#         self.send_dispatch(dispatch_to_send)
#
#         self.receive_dispatch()
#
#         new_dispatch_display = DispatchDisplay(Dispatch(), received=False)
#         self.query_one(ClientMainDisplay).add_dispatch_display(new_dispatch_display)
#
#         self.query_one(Countdown).cancel()
#         self.query_one(Countdown).start(SECONDS_BETWEEN_DISPATCHES)
#
#     def action_log_in(self) -> None:
#         # TODO: handle identification cards
#         self.notify(title="Provide identification", message=f"Place your identification card on the reader",
#                     severity="information", timeout=5.0)
#         self.current_user = USERS["test_encrypted_user"]
#         if self.current_user.encryption_on:
#             self.query_one(ClientMainDisplay).decrypt_all_dispatches_of_user(self.current_user)
#             self.query_one(ClientMainDisplay).refresh(recompose=True)
#         self.query_one(UserInfoDisplay).update(f"{self.current_user.user_id} is logged in")
#         self.notify(title=f"Welcome", message=f"You successfully logged in as {self.current_user.user_id}",
#                     severity="information",
#                     timeout=5.0)
#         self.logger.info(f"User {self.current_user} logged in")
#
#     def action_log_out(self) -> None:
#         self.refresh_bindings()
#         if self.current_user.encryption_on:
#             self.query_one(ClientMainDisplay).encrypt_all_dispatches_of_user(self.current_user)
#             self.query_one(ClientMainDisplay).refresh(recompose=True)
#         past_user = self.current_user
#         self.current_user = USERS["no_account"]
#         self.query_one(UserInfoDisplay).update(f"User ID: {self.current_user.user_id} (nobody logged in)")
#         self.notify(title="Goodbye", message="You successfully logged out", severity="information", timeout=5.0)
#         self.logger.info(f"User {past_user} logged out")
#
#
#     def action_write_message(self) -> None:
#         self.refresh_bindings()
#         if self.current_user.user_id == 0:
#             self.notify(message="You are not logged in. Log in to write messages.", severity="error", timeout=5.0)
#             self.logger.warning("Somebody tried to write message without logging in")
#         else:
#             message_input_widget = TextMessageInput()
#             self.mount(message_input_widget)
#             message_input_widget.scroll_visible()
#
#     def compose(self) -> ComposeResult:
#         yield Header(show_clock=True)
#         yield Footer()
#         yield UserInfoDisplay(f"User ID: {self.current_user.user_id} (nobody logged in)")
#         yield TimeDisplay()
#         yield Countdown()
#         yield ClientMainDisplay()



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
