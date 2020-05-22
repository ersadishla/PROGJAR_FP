import socket
import time
import sys
import asyncore
import logging
import time

class BackendList:
    def __init__(self):
        self.last_port = 9001
        self.servers = [
            ('127.0.0.1',9001),
            ('127.0.0.1',9002),
            ('127.0.0.1',9003),
            ('127.0.0.1',9004),
        ]
        self.current = 0
    def getserver(self):
        s = self.servers[self.current]
        self.current = (self.current + 1) % len(self.servers) 
        # if (self.current>=len(self.servers)):
        # 	self.current=0
        return s
    # def moreserver(self):
    # 	if (self.current_worker <= self.max_worker):
    # 		self.servers.append(('127.0.0.1', self.last_port))
    # 		logging.warning("current worker {}" . format(self.current_worker))
        # else:
        # 	self.current_worker = self.max_worker



class Backend(asyncore.dispatcher_with_send):
    def __init__(self,targetaddress):
        asyncore.dispatcher_with_send.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect(targetaddress)
        self.connection = self

    def handle_read(self):
        try:
            self.client_socket.send(self.recv(8192))
        except:
            pass
    def handle_close(self):
        try:
            self.close()
            self.client_socket.close()
        except:
            pass


class ProcessTheClient(asyncore.dispatcher):
    def handle_read(self):
        data = self.recv(8192)
        if data:
            self.backend.client_socket = self
            self.backend.send(data)
    def handle_close(self):
        self.close()

class Server(asyncore.dispatcher):
    def __init__(self,portnumber):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind(('',portnumber))
        self.listen(5)
        self.bservers = BackendList()
        self.req = 0
        logging.warning("load balancer running on port {}" . format(portnumber))

    def handle_accept(self):
        pair = self.accept()
        if pair is not None:
            sock, addr = pair
            logging.warning("connection from {}" . format(repr(addr)))

            #menentukan ke server mana request akan diteruskan
            bs = self.bservers.getserver()
            logging.warning("koneksi dari {} diteruskan ke {}" . format(addr, bs))
            
            vacant = True
            while(vacant):
                try:
                    backend = Backend(bs)
                    break
                except ConnectionRefusedError:
                    bs = self.bservers.getserver()
                    continue

            #mendapatkan handler dan socket dari client
            handler = ProcessTheClient(sock)
            handler.backend = backend


def main():
    portnumber=44444
    try:
        portnumber=int(sys.argv[1])
    except:
        pass
    svr = Server(portnumber)
    asyncore.loop()

if __name__=="__main__":
    main()


