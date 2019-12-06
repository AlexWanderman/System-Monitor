from socket import *
from threading import Thread
from datetime import datetime as dt
from sqlite3 import connect
import re


class DataBaseConnection:
    '''Класс для обмена данными с базой данных

    db_path -> str (Путь к файлу БД или его название).

    Подключается к файлу БД, создает или открывает файл, осуществляет запись и
    чтение данных.

    '''
    def __init__(self, db_path):
        self.db_path = db_path

        self.recpu = re.compile(r'type:cpu prc:([0-9]+)')
        self.reram = re.compile(r'type:ram ttl:([0-9]+) avl:([0-9]+) ' +
                                r'prc:([0-9]+)')
        self.reswap = re.compile(r'type:swp ttl:([0-9]+) free:([0-9]+) ' +
                                 r'prc:([0-9]+)')
        self.redisk = re.compile(r'type:dsk ltr:([a-z]) ttl:([0-9]+) ' +
                                 r'free:([0-9]+) prc:([0-9]+)')

    def authentication(self, name, key):
        con = connect(self.db_path)
        cur = con.cursor()

        cur.execute('''select count(log) from Login
                       where log = ? and pas = ?''',
                    [name, key])
        i = cur.fetchall()[0][0]

        if i > 1:
            raise ValueError('Имя не уникально!')

        if i is 0:
            return False

        return True

    def write_data(self, name, tp, msg):
        con = connect(self.db_path)
        cur = con.cursor()

        if tp == 'test':
            print('~ тест')
            return '+'

        elif tp == 'cpu':
            prc = self.recpu.findall(msg)[0]
            print(f'name:{name} prc:{prc}')
            cur.execute('insert into CPU values(?, ?, ?)',
                        [name, prc, dt.now()])

        elif tp == 'ram':
            ttl, avl, prc = self.reram.findall(msg)[0]
            print(f'name:{name} ttl:{ttl} avl:{avl} prc:{prc}')
            cur.execute('insert into RAM values(?, ?, ?, ?, ?)',
                        [name, ttl, avl, prc, dt.now()])

        elif tp == 'swp':
            ttl, free, prc = self.reswap.findall(msg)[0]
            print(f'name:{name} ttl:{ttl} free:{free} prc:{prc}')
            cur.execute('insert into Swap values(?, ?, ?, ?, ?)',
                        [name, ttl, free, prc, dt.now()])

        elif tp == 'dsk':
            ltr, ttl, free, prc = self.redisk.findall(msg)[0]
            print(f'name:{name} ltr:{ltr} ttl:{ttl} free:{free} prc:{prc}')
            cur.execute('insert into Disk values(?, ?, ?, ?, ?, ?)',
                        [name, ltr, ttl, free, prc, dt.now()])

        else:
            print('~ ОШИБКА КОМАНДЫ!')
            return '-'

        con.commit()
        print('+ запись')

        return '+'


class Server:
    '''Класс для обмена данными с клиентами

    ip -> str (IP адрес сервера);
    port -> int (Порт сервера);
    db_path -> str (Путь к файлу БД или его название).

    Сервер ведет обмен данными с клиентами, а для работы с БД использует
    экземпляр DataBaseConnection.

    '''
    def __init__(self, ip, port, db_path):
        self.address = ip
        self.port = port
        self.db_conn = DataBaseConnection(db_path)

        self.msg_size = 512
        self.relogin = re.compile(
            r'name:([a-zA-Zа-яА-Я0-9_]+) ' +
            r'key:([a-zA-Zа-яА-Я0-9_!@#$%^&*()\[\]{}]+)'
        )
        self.retype = re.compile(r'type:([a-z]+)')

        print('Запуск сервера...')

        st = Thread(target=self.server, args=())
        st.start()

    def server(self):
        # Настройка соединения
        server_socket = socket(AF_INET, SOCK_STREAM)
        server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        server_socket.bind((self.address, self.port))
        server_socket.listen()

        print('Жду клиентов...')

        # Обработка клиентов
        while True:
            client_socket, addr = server_socket.accept()

            print(f'Идет подключение {addr}!')

            t = Thread(target=self.client_handler,
                       args=(client_socket, addr),
                       daemon=True)
            t.start()

            print(f'Поток запущен {addr}!')

    # ! Переделать в певрвую очередь !
    def client_handler(self, client_socket, addr):
        # Аутентификация
        try:
            request = client_socket.recv(self.msg_size)
        except ConnectionResetError:
            request = None

        if request:
            login = self.relogin.findall(request.decode())[0]

            if self.db_conn.authentication(login[0], login[1]):
                print(f'Аутентификация {addr} -> {login[0]}!')
                client_socket.send('Аутентификация пройдена'.encode())
            else:
                print(f'Ошибка имени или ключа {addr} -> {login[0]}!')
                client_socket.send('Ошибка в имени или ключе'.encode())
                client_socket.close()
                print(f'Соединение с {addr} закрыто!')
                return
        else:
            client_socket.close()
            print(f'Соединение с {addr} закрыто!')
            return

        # Обработка запросов клиента
        while True:
            try:
                request = client_socket.recv(self.msg_size)
            except ConnectionResetError:
                request = None

            if request:
                # Обмен сообщениями
                msg = request.decode()
                print(f'Сообщение "{msg}" от {login[0]} {addr}!')

                tp = self.retype.findall(msg)[0]

                print(f'tp={tp}')

                r = self.db_conn.write_data(login[0], tp, msg)

                client_socket.send(r.encode())
            else:
                client_socket.close()
                print(f'Соединение с {addr} закрыто!')
                return


if __name__ == "__main__":
    ip = 'localhost'
    port = 5000
    dp_path = 'test.sqlite3'
    server = Server(ip, port, dp_path)
