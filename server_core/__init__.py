'''Модуль для серверной части приложения

Содержит в себе интерфейс для работы с базой данных, сервер, пресеты для
создания базы данных и обработки сообщений от клиентов.

'''

from .server import Server
from .storage import Storage


def test_mode():
    import doctest
    doctest.testfile('storage_test.txt', verbose=True)
    input('Нажмите enter для выхода...')
