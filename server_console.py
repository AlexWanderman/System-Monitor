'''Интерфейс работы с сервером'''

from server_core import Server

if __name__ == "__main__":
    server = Server()
    server.start()

    print(server.address)

    while True:
        try:
            r = eval(f'server.storage.{input("> ")}')
        except Exception as e:
            r = e

        if r == []:
            print('[]')
        elif r is list:
            for n in r[:30]:
                print(n)
        else:
            print(r)
