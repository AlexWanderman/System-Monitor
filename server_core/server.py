'''Реализует функции работы с клиентами'''

import re
import socket
from datetime import datetime as dt
from threading import Thread

from .storage import Storage


class Server(Thread):
    '''Сервер'''
    def __init__(self):
        Thread.__init__(self)

        self.name = 'thread_server'
        # socket.gethostname()
        self.address = 'localhost'
        self.port = 80
        self.msg_size = 512
        self.storage = Storage('sys_monitor.db')

        self.relogin = re.compile(
            r'name:([a-zA-Zа-яА-Я0-9_]+) ' +
            r'key:([a-zA-Zа-яА-Я0-9_!@#$%^&*()\[\]{}]+)'
        )

        self.storage.setup_database()

    def _client_accepter(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.address, self.port))
        server_socket.listen()

        while True:
            client_socket, addr = server_socket.accept()

            t = Thread(target=self._client_handler,
                       args=(client_socket, addr),
                       name=f'client_{addr}')
            t.start()

    def _client_handler(self, client_socket, addr):
        try:
            request = client_socket.recv(self.msg_size)
        except ConnectionResetError:
            request = None

        if request:
            login = self.relogin.findall(request.decode())[0]
            r = self.storage.check_user(login[0], login[1])

            if type(r) is list:
                repl = '+'
            else:
                repl = '-'

            client_socket.send(repl.encode())

        else:
            client_socket.close()
            return

        while True:
            try:
                request = client_socket.recv(self.msg_size)
            except ConnectionResetError:
                request = None

            if request:
                req = request.decode()
                r = self.storage.add_user_data(login[0], req)

                if type(r) is list:
                    repl = '+'
                else:
                    repl = '-'

                client_socket.send(repl.encode())
            else:
                client_socket.close()
                return

    def run(self):
        self._client_accepter()
