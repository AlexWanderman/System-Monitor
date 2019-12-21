'''Интерфейс работы с сервером'''

from server_core import Server

if __name__ == "__main__":
    server = Server()
    server.start()

    while True:
        try:
            r = eval(f'server.storage.{input("> ")}')
        except Exception as e:
            r = e

        print(r)
