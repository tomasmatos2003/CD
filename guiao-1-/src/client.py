"""CD Chat client program"""

import fcntl
import logging
import os
import selectors
import sys
import socket

from .protocol import CDProto, CDProtoBadFormat, TextMessage

logging.basicConfig(filename=f"{sys.argv[0]}.log", level=logging.DEBUG)

class Client:
    """Chat Client process."""

    def __init__(self, name: str = "Foo"):
        """Initializes chat client."""
        self.name = name
        self.host = 'localhost'
        self.port = 5006

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  

        self.sel = selectors.DefaultSelector()
        
        self.CDProto = CDProto()

        self.channel = None

    def recv_data(self, sock):
        data = self.CDProto.recv_msg(sock)

        if data.command_type == "message":
            msg = str(data).split('"')[7]
            
            print(msg[:-1])   # tirar \n
        elif data.command_type == "join":
            msg = str(data).split('"')
            
            if self.channel != None:
                print("--------------- Joined channel: " , msg[7] , " ---------------")
         
    

    def connect(self):
        """Connect to chat server and setup stdin flags."""
        print('{} connected ...'.format(self.name))
        print("--------------- Joined channel: public ---------------")

        self.client_socket.connect((self.host, self.port))
        self.client_socket.setblocking(False)   
        self.sel.register(self.client_socket, selectors.EVENT_READ, self.recv_data)

        register = self.CDProto.register(self.name)
        self.CDProto.send_msg(self.client_socket, register)

    
    def got_keyboard_data(self, stdin):
        
        data = stdin.read()
        if str(data) == 'exit\n':
            
            data =  self.name + ": " + data

            msg = self.CDProto.message(data, self.channel) 
            self.CDProto.send_msg(self.client_socket, msg)
            self.client_socket.close()
            sys.exit(0)

        elif str(data)[:5] == '/join':
          
            if len(str(data)) < 8:
                print("You need to insert a channel name")
            else:
                self.channel = str(data)[6:-1]
              
                join = self.CDProto.join(self.channel)
                self.CDProto.send_msg(self.client_socket, join)

        else:
            data =  self.name + ": " + data

            msg = self.CDProto.message(data, self.channel) 
            self.CDProto.send_msg(self.client_socket, msg)
        
          

    def loop(self):
        """Loop indefinetely."""
        
        orig_fl = fcntl.fcntl(sys.stdin, fcntl.F_GETFL)
        fcntl.fcntl(sys.stdin, fcntl.F_SETFL, orig_fl | os.O_NONBLOCK)
       
        self.sel.register(sys.stdin, selectors.EVENT_READ, self.got_keyboard_data)

        while True:
           
            for k, mask in self.sel.select():
                callback = k.data
                callback(k.fileobj)
