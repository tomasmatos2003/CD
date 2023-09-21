"""Protocol for chat server - Computação Distribuida Assignment 1."""
import json
from datetime import datetime
from socket import socket


class Message:
    """Message Type."""
    def __init__(self, command_type):
        self.command_type = command_type
    
    def __repr__(self) -> str:
        return f'"command": "{self.command_type}"'
    
class JoinMessage(Message):
    """Message to join a chat channel."""
    """{"command": "join", "channel": "#cd"}"""

    def __init__(self, command_type, channel):
        super().__init__("join")
        self.channel = channel

    def __repr__(self) -> str:
        return f'{{{super().__repr__()}, "channel": "{self.channel}"}}'


class RegisterMessage(Message):
    """Message to register username in the server."""
    """{"command": "register", "user": "student"}"""
   
    def __init__(self, command_type, user):
        super().__init__("register")
        self.user = user

    def __repr__(self) -> str:
        return f'{{{super().__repr__()}, "user": "{self.user}"}}'

    
class TextMessage(Message):
    """Message to chat with other clients."""
    """{"command": "message", "message": "Hello World", “channel”:“#cd”, " "ts": 1615852800}"""

    def __init__(self, command_type, message, channel, ts):
        super().__init__("message")
        self.message = message
        self.channel = channel
        self.ts = ts

    def __repr__(self) -> str:
       
        if self.channel != None:
            return f'{{{super().__repr__()}, "message": "{self.message}", "channel": "{self.channel}", "ts": {self.ts}}}'
        else:
            return f'{{{super().__repr__()}, "message": "{self.message}", "ts": {self.ts}}}'
            
class CDProto:
    """Computação Distribuida Protocol."""

    @classmethod
    def register(cls, username: str) -> RegisterMessage:
        """Creates a RegisterMessage object."""

        return RegisterMessage("register", username)
    
    @classmethod
    def join(cls, channel: str) -> JoinMessage:
        """Creates a JoinMessage object."""

        return JoinMessage("join", channel)

    @classmethod
    def message(cls, message: str, channel: str = None) -> TextMessage:
        """Creates a TextMessage object."""
       
        return TextMessage("message", message, channel, int(datetime.now().timestamp()))
    
    @classmethod
    def send_msg(cls, connection: socket, msg: Message):
        """Sends through a connection a Message object."""

        if msg.command_type == "register":
            msg_dic = {"command": msg.command_type, "user": msg.user}
            msg_json = json.dumps(msg_dic)

        elif msg.command_type == "join":
            msg_dic = {"command": msg.command_type, "channel": msg.channel}
            msg_json = json.dumps(msg_dic)

        elif msg.command_type == "message":
           
            if msg.channel is None:
                msg_dic = {"command": msg.command_type, "message": msg.message, "ts": msg.ts}
                msg_json = json.dumps(msg_dic)
               
            else:
                msg_dic = {"command": msg.command_type, "message": msg.message, "channel": msg.channel, "ts": msg.ts}
                msg_json = json.dumps(msg_dic)
        
        tamanho = len(msg_json)
        cod_2by = tamanho.to_bytes(2, byteorder='big')

        connection.send(cod_2by + msg_json.encode("utf-8"))
        

    @classmethod
    def recv_msg(cls, connection: socket) -> Message:
        """Receives through a connection a Message object."""
        try:
            cod_2by = connection.recv(2)
            tamanho = int.from_bytes(cod_2by, byteorder='big')

            msg_json = connection.recv(tamanho).decode("utf-8")
            msg_dic = json.loads(msg_json)

        except json.JSONDecodeError as err:
            raise CDProtoBadFormat(msg_json)

        if msg_dic["command"] == "register":
            return RegisterMessage("register", msg_dic["user"])
        
        elif msg_dic["command"] == "join":
            return JoinMessage("join", msg_dic["channel"])
        
        elif msg_dic["command"] == "message":

            if msg_dic.get("channel") is None:
                return TextMessage("message", msg_dic["message"], None, msg_dic["ts"])
            else:
                return TextMessage("message", msg_dic["message"], msg_dic["channel"], msg_dic["ts"])

        else:
            raise CDProtoBadFormat(msg_json.encode("utf-8"))


class CDProtoBadFormat(Exception):
    """Exception when source message is not CDProto."""

    def __init__(self, original_msg: bytes=None) :
        """Store original message that triggered exception."""
        self._original = original_msg

    @property
    def original_msg(self) -> str:
        """Retrieve original message as a string."""
        return self._original.decode("utf-8")
