"""CD Chat server program."""
import logging
import selectors
import socket

from .protocol import CDProto, CDProtoBadFormat

logging.basicConfig(filename="server.log", level=logging.DEBUG)


class Server:
    """Chat Server process."""
    def __init__(self, name: str = "Foo"):
        """Initializes chat server."""

        self.host = 'localhost' 
        self.port = 5006

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.host, self.port))

        self.socket.listen(100)
        
        self.sel = selectors.DefaultSelector()
        self.sel.register(self.socket, selectors.EVENT_READ, self.accept_client)

        self.clients = {}
        self.clients_names = {}
        self.clients_channels = {}

    def accept_client(self, sock, mask ):
        """Accepts new connection."""

        (conn, addr) = sock.accept()  

        conn.setblocking(False)
        
        self.sel.register(conn, selectors.EVENT_READ, self.read)
        self.clients[conn] = addr

        msg = CDProto.recv_msg(conn)
        
        username = str(msg).split('"')[7]
        
        print("RegisterMessage: " + str(msg)  + " connected ...")
        self.clients_names[conn] = username 

        self.clients_channels[conn] = None
        

    def read(self, conn, mask):
        """Reads data from connection."""
        try:
            data = CDProto.recv_msg(conn)
        except CDProtoBadFormat:
            print('closing', conn)
            self.sel.unregister(conn)
            conn.close()
            del self.clients[conn]
            return
        
        if data.command_type == "message":
            print(data)
            msg = str(data).split('"')[7]

            print(f"received message from {self.clients_names[conn]}: {msg}")
            
            if msg[-5:-1] == 'exit':
                print('closing', self.clients_names[conn])
                self.sel.unregister(conn)
                conn.close()
                del self.clients[conn]
                del self.clients_names[conn]
                del self.clients_channels[conn]
                return
            
            for client_sock in self.clients.keys():
                if client_sock != conn and self.clients_channels[client_sock] == self.clients_channels[conn]:
                    print('sending to', self.clients_names[client_sock],": ", msg)
                    
                    CDProto.send_msg(client_sock, data)

        elif data.command_type == "join":
            
            channel = str(data).split('"')[7]
            
            self.clients_channels[conn] = channel
            print("JoinMessage: Client joined:", channel , "(" , self.clients_names[conn] , ")")
   
            join = CDProto.join(channel)
            CDProto.send_msg(conn, join)

        else:
            print('closing', conn)
            self.sel.unregister(conn)
            conn.close()
            del self.clients[conn]


    def loop(self):
        """Loop indefinetely."""
        
        while True:
            events = self.sel.select()
            for key, mask in events:
                callback = key.data
                callback(key.fileobj, mask)