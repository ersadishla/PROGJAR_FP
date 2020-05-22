from typing import List
import socket
import threading
import time
import sys
import logging
import psutil
from multiprocessing import Process, Queue

from http import HttpServer

q: Queue = Queue()
httpserver = HttpServer()


class ProcessTheClient(threading.Thread):
    def __init__(self, connection, address):
        self.connection = connection
        self.address = address
        super().__init__()

    def run(self):
        rcv = ""
        while True:
            try:
                data = self.connection.recv(32)
                if data:
                    # merubah input dari socket (berupa bytes) ke dalam string
                    # agar bisa mendeteksi \r\n
                    d = data.decode()
                    rcv = rcv + d
                    if rcv[-2:] == '\r\n':
                        # end of command, proses string
                        # logging.warning("data dari client: {}".format(rcv))
                        hasil = httpserver.proses(rcv)
                        # hasil akan berupa bytes
                        # untuk bisa ditambahi dengan string, maka string harus di encode
                        hasil = hasil + "\r\n\r\n".encode()
                        # logging.warning("balas ke  client: {}".format(hasil))
                        # hasil sudah dalam bentuk bytes
                        self.connection.sendall(hasil)
                        rcv = ""
                        break
                else:
                    break
            except OSError as e:
                pass
        self.connection.close()


class Worker(Process):
    def __init__(self, id: int, queue: Queue):
        super().__init__()
        self.queue = queue
        self.clients: List[ProcessTheClient] = []
        self.id = id

    def run(self) -> None:
        while True:
            data = self.queue.get()
            # print(self.id, data)

            clt = ProcessTheClient(data[0], data[1])
            clt.start()
            self.clients.append(clt)


class WorkerManager:
    def __init__(self, max_worker=5):
        self.workers = []
        self.max_worker = max_worker

    def generate(self):
        for i in range(self.max_worker):
            worker = Worker(i, q)
            worker.daemon = True
            worker.start()
            self.workers.append(worker)


class Server(threading.Thread):
    def __init__(self, portnumber):
        self.the_clients = []
        self.portnumber = portnumber
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        threading.Thread.__init__(self)

    def run(self):
        self.my_socket.bind(('0.0.0.0', self.portnumber))
        self.my_socket.listen(1)
        while True:
            connection, client_address = self.my_socket.accept()
            logging.warning("connection from {}".format(client_address))

            q.put((connection, client_address))


if __name__ == "__main__":
    portnumber = 44445
    try:
        worker_count = psutil.cpu_count()
    except:
        worker_count = 8

    wm = WorkerManager(worker_count)
    wm.generate()

    try:
        portnumber = int(sys.argv[1])
    except:
        pass
    svr = Server(portnumber)
    svr.start()
