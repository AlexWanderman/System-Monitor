from socket import *
from threading import Thread
from time import sleep

import psutil


class Spectator:
    '''Класс сборшик данных о системе

    Получает запрос о том, какие данные считать и возвращает сообщение в виде
    str для отправки на сервер.
    '''
    def get_data(self, tp):
        '''cpu -> str, ram -> str, swp -> str, disk -> list.'''
        if tp == 'cpu':
            prc = int(psutil.cpu_percent())
            return f'type:cpu prc:{prc}'

        elif tp == 'ram':
            ram = psutil.virtual_memory()

            ttl = ram.total
            avl = ram.available
            prc = int(ram.percent)

            return f'type:ram ttl:{ttl} avl:{avl} prc:{prc}'

        elif tp == 'swp':
            swp = psutil.swap_memory()

            ttl = swp.total
            free = swp.free
            prc = int(swp.percent)

            return f'type:swp ttl:{ttl} free:{free} prc:{prc}'

        # Возвращает список
        elif tp == 'dsk':
            drives = psutil.disk_partitions(all=False)
            paths = []
            result = []

            for d in drives:
                if d.opts == 'rw,fixed':
                    paths.append(d.mountpoint)

            for p in paths:
                dsk = psutil.disk_usage(p)

                ltr = p[0].lower()
                ttl = dsk.total
                free = dsk.free
                prc = int(dsk.percent)

                t = f'type:dsk ltr:{ltr} ttl:{ttl} free:{free} prc:{prc}'
                result.append(t)

            return result

        else:
            raise TypeError('Неправильно указан запрошенный тип')


class Client:
    '''Класс клиента

    ip -> str (IP адрес сервера);
    port -> int (Порт сервера);
    name -> str (Имя учетной записи);
    key -> str (Ключ учетной записи).

    Клиент аутентифицируется на сервере, при удачной аутентификации собирает
    данные о загруженности системы и отправляет на сервер через определенный
    интервал времени.

    '''
    def __init__(self, ip, port, name, key):
        self.address = ip
        self.port = port
        self.name = name
        self.key = key

        self.msg_size = 512
        self.client_socket = None
        self.spectator = Spectator()

        # Период отправки данных по параметрам
        self.cpu_timer = 6
        self.ram_timer = 6
        self.swp_timer = 12
        self.dsk_timer = 30

        self.client()

    def client(self):
        # Настройка соединения
        self.client_socket = socket(AF_INET, SOCK_STREAM)
        self.client_socket.connect((self.address, self.port))

        # Аутентификация
        login = f'name:{self.name} key:{self.key}'
        self.client_socket.send(login.encode())
        respr = self.client_socket.recv(self.msg_size)

        if respr.decode() != 'Аутентификация пройдена':
            print(respr.decode())
            self.client_socket.close()
            return

        print(respr.decode())

        # Запуск потоков, для отправки данных по параметрам
        Thread(target=self.monitor, args=('cpu', self.cpu_timer)).start()
        Thread(target=self.monitor, args=('ram', self.ram_timer)).start()
        Thread(target=self.monitor, args=('swp', self.swp_timer)).start()
        # Thread(target=self.monitor, args=('dsk', self.dsk_timer)).start()

    def monitor(self, tp, period):
        while True:
            data = self.spectator.get_data(tp)
            self.client_socket.send(data.encode())
            respr = self.client_socket.recv(self.msg_size).decode()

            if respr == '-':
                print(f'Сервер сообщает об ошибке при попытке записи {data}')

            elif respr == '+':
                print(f'Запись успешна {data}')

            else:
                print(f'Нераспознаный ответ сервера - {respr}')

            sleep(period)


if __name__ == "__main__":
    ip = 'localhost'
    port = 5000
    name = input('name: ')
    key = input('key: ')
    client = Client(ip, port, name, key)
