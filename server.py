import re
from datetime import datetime as dt
from socket import AF_INET, SO_REUSEADDR, SOCK_STREAM, SOL_SOCKET, socket
from sqlite3 import DatabaseError, IntegrityError, connect
from threading import Thread


class DataBaseConnection:
    '''Класс для обмена данными с базой данных

    db_path -> str (Путь к файлу БД или его название).

    Подключается к файлу БД, создает или открывает файл, осуществляет запись и
    чтение данных.

    '''
    def __init__(self, db_path):
        self.db_path = db_path

        self.re_cpu = re.compile(r'type:cpu prc:([0-9]+)')
        self.re_ram = re.compile(r'type:ram ttl:([0-9]+) avl:([0-9]+) ' +
                                 r'prc:([0-9]+)')
        self.re_swap = re.compile(r'type:swp ttl:([0-9]+) free:([0-9]+) ' +
                                  r'prc:([0-9]+)')
        self.re_disk = re.compile(r'type:dsk ltr:([a-z]) ttl:([0-9]+) ' +
                                  r'free:([0-9]+) prc:([0-9]+)')

        self.sql_login = '''CREATE TABLE "Login" (
                            "name" TEXT NOT NULL,
                            "key" TEXT NOT NULL,
                            "is_active" INTEGER CHECK(
                                is_active = 0 or
                                is_active = 1
                                ),
                            PRIMARY KEY("name"))'''

        self.sql_cpu = '''CREATE TABLE "CPU" (
                            "name" TEXT NOT NULL,
                            "prc" INTEGER NOT NULL CHECK(prc>=0 and prc<=100),
                            "date" TEXT NOT NULL,
                            FOREIGN KEY("name") REFERENCES "Login"("name")
                                ON DELETE CASCADE)'''

        self.sql_ram = '''CREATE TABLE "RAM" (
                            "name" TEXT NOT NULL,
                            "ttl" INTEGER NOT NULL CHECK(ttl >= 0),
                            "avl" INTEGER NOT NULL CHECK(avl >= 0),
                            "prc" INTEGER NOT NULL CHECK(
                                prc >=0 and
                                prc <= 100
                                ),
                            "date" TEXT NOT NULL,
                            FOREIGN KEY("name") REFERENCES "Login"("name")
                                ON DELETE CASCADE)'''

        self.sql_swap = '''CREATE TABLE "Swap" (
                            "name" TEXT NOT NULL,
                            "ttl" INTEGER NOT NULL CHECK(ttl >= 0),
                            "free" INTEGER NOT NULL CHECK(free >= 0),
                            "prc" INTEGER NOT NULL CHECK(
                                prc >= 0 and
                                prc <= 100
                                ),
                            "date" TEXT NOT NULL,
                            FOREIGN KEY("name") REFERENCES "Login"("name")
                                ON DELETE CASCADE)'''

        self.sql_disk = '''CREATE TABLE "Disk" (
                            "name" TEXT NOT NULL,
                            "ltr" TEXT NOT NULL,
                            "ttl" INTEGER NOT NULL CHECK(ttl >= 0),
                            "free" INTEGER NOT NULL CHECK(free >= 0),
                            "prc" INTEGER NOT NULL CHECK(
                                prc >= 0 and
                                prc <= 100
                                ),
                            "date" TEXT NOT NULL,
                            FOREIGN KEY("name") REFERENCES "Login"("name")
                            ON DELETE CASCADE)'''

        self.sql_log = '''CREATE TABLE "Log" (
                            "name" TEXT NOT NULL,
                            "msg" TEXT NOT NULL,
                            "is_added" INTEGER NOT NULL CHECK(
                                is_added = 0 or
                                is_added = 1
                                ),
                            "error" TEXT,
                            "date" TEXT NOT NULL,
                            FOREIGN KEY("name") REFERENCES "Login"("name")
                            ON DELETE CASCADE);'''

        self.tables = {
            'Login': self.sql_login,
            'CPU': self.sql_cpu,
            'RAM': self.sql_ram,
            'Swap': self.sql_swap,
            'Disk': self.sql_disk,
            'Log': self.sql_log,
        }

        # Проверка БД
        self.setup_database()

    def _try_to_write(self, msg, data=()):
        con = connect(self.db_path)
        cur = con.cursor()

        try:
            cur.execute(msg, data)
        except DatabaseError as e:
            con.rollback()
            print(f'ОШИБКА записи!\n{e}')
            return False
        else:
            con.commit()
            print(f'Запись произведена!')
            return True
        finally:
            con.close()

    def _try_to_read(self, msg, data=()):
        con = connect(self.db_path)
        cur = con.cursor()

        r = cur.execute(msg, data).fetchall()
        con.close()

        return r

    def setup_database(self):
        con = connect(self.db_path)
        cur = con.cursor()

        msg = 'select * from sqlite_master where type = "table"'
        names = [x[1] for x in self._try_to_read(msg)]

        for table, sql in self.tables.items():
            if table in names:
                continue

            cur.execute(sql)
            con.commit()

        con.close()

    def authentication(self, name, key):
        msg = '''select count(name) from Login
            where name = ? and key = ? and is_active = 1'''
        data = [name, key]
        r = self._try_to_read(msg, data)
        i = r[0][0]

        if i > 1:
            # Эта ошибка не может возникнуть (должно совпасть имя и пароль)
            raise ValueError('Имя не уникально!')

        if i is 0:
            return False

        return True

    def create(self, name, key):
        msg = 'insert into Login values(?, ?, 1)'
        data = [name, key]

        return self._try_to_write(msg, data)

    def delete(self, name):
        msg = 'delete from Login where name = ?'
        data = [name]

        return self._try_to_write(msg, data)

    def set_activity(self, name, is_active):
        i = 1 if is_active else 0
        msg = 'update Login set is_active = ? where name = ?'
        data = [i, name]

        return self._try_to_write(msg, data)

    def write_data(self, name, tp, msg):
        # Перенести определение типа сюда
        if tp == 'cpu':
            prc = self.re_cpu.findall(msg)[0]
            print(f'name:{name} tp:{tp} prc:{prc}')

            msg = 'insert into CPU values(?, ?, ?)'
            data = [name, prc, dt.now()]
            r = self._try_to_write(msg, data)

        elif tp == 'ram':
            ttl, avl, prc = self.re_ram.findall(msg)[0]
            print(f'name:{name} tp:{tp} ttl:{ttl} avl:{avl} prc:{prc}')

            msg = 'insert into Swap values(?, ?, ?, ?, ?)'
            data = [name, ttl, avl, prc, dt.now()]
            r = self._try_to_write(msg, data)

        elif tp == 'swp':
            ttl, free, prc = self.re_swap.findall(msg)[0]
            print(f'name:{name} tp:{tp} ttl:{ttl} free:{free} prc:{prc}')

            msg = 'insert into Swap values(?, ?, ?, ?, ?)'
            data = [name, ttl, free, prc, dt.now()]
            r = self._try_to_write(msg, data)

        elif tp == 'dsk':
            ltr, ttl, free, prc = self.re_disk.findall(msg)[0]
            print(f'name:{name} tp:{tp} ltr:{ltr} ttl:{ttl} ' +
                  f'free:{free} prc:{prc}')

            msg = 'insert into Disk values(?, ?, ?, ?, ?, ?)'
            data = [name, ltr, ttl, free, prc, dt.now()]
            r = self._try_to_write(msg, data)

        else:
            print(f'ОШИБКА команды "{msg}"!')
            r = False

        return '+' if r else '-'


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
        # Перенести в БД
        self.relogin = re.compile(
            r'name:([a-zA-Zа-яА-Я0-9_]+) ' +
            r'key:([a-zA-Zа-яА-Я0-9_!@#$%^&*()\[\]{}]+)'
        )
        self.retype = re.compile(r'type:([a-z]+)')

        print('Запуск сервера...')

        # Запуск сервера
        self.server()

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

                r = self.db_conn.write_data(login[0], tp, msg)

                client_socket.send(r.encode())
            else:
                client_socket.close()
                print(f'Соединение с {addr} закрыто!')
                return


if __name__ == "__main__":
    ip = 'localhost'
    port = 5000
    dp_path = 'test.db'
    server = Server(ip, port, dp_path)
