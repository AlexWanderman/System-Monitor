'''Реализует функции работы с базой данных'''

import re
from datetime import datetime as dt
from sqlite3 import DatabaseError, connect

from .sql_setup import Setup


class Storage:
    '''База данных'''

    def __init__(self, file_path):
        settings = Setup()

        self.file_path = file_path
        self.tables = {
            "Login": settings.sql_login,
            "CPU": settings.sql_cpu,
            "RAM": settings.sql_ram,
            "Swap": settings.sql_swap,
            "Disk": settings.sql_disk,
        }
        self.exprs = {
            "Login": settings.re_login,
            "CPU": settings.re_cpu,
            "RAM": settings.re_ram,
            "Swap": settings.re_swap,
            "Disk": settings.re_disk,
            "Type": settings.re_type,
        }

    # === Внутренние функции ===
    def _query(self, msg, data=()):
        '''Функция для работы с БД.'''

        # Удачно -> [...]
        # Неудачно -> DatabaseError
        con = connect(self.file_path)

        try:
            with con:
                cur = con.cursor()
                r = cur.execute(msg, data)

        except DatabaseError as e:
            con.rollback()
            return e

        else:
            con.commit()
            return r.fetchall()

        finally:
            con.close()

    # === Настройки ===
    def setup_database(self):
        '''Заполняет файл БД недостающими таблицами.'''

        # Список таблиц
        msg = 'select * from sqlite_master where type = "table"'
        r = self._query(msg)

        if r is DatabaseError:
            raise r

        names = [x[1] for x in r]

        # Поиск отсутствующих таблиц по названиям
        # FIXME Возможно совпадение имени, но не содержания
        for name, msg in self.tables.items():
            if name in names:
                continue

            r = self._query(msg)

            if r is DatabaseError:
                raise r

        # Удачное выполнение
        return []

    # === Учетная запись ===
    def create_user(self, name, key, is_active=True):
        '''Создает новую учетную запись.'''

        msg = 'insert into Login values(?, ?, 1)'
        data = [name, key]

        return self._query(msg, data)

    def show_users(self, with_key=False, only_active=False):
        '''Возвращает список учетных записей и, если нужно, пароли.'''

        if with_key:
            t1 = '*'
        else:
            t1 = 'name, is_active'

        if only_active:
            msg = f'select {t1} from Login where is_active = 1'
        else:
            msg = f'select {t1} from Login'

        return self._query(msg)

    def check_user(self, name, key):
        '''Проверяет имя и ключ'''

        msg = 'select name, is_active from Login where name = ? and key = ?'
        data = [name, key]

        return self._query(msg, data)

    def delete_user(self, name):
        '''Удаляет учетную запись и все её данные.'''

        # FIXME Не проверяет наличие записи
        msg = 'delete from Login where name = ?'
        data = [name]

        return self._query(msg, data)

    def edit_user(self, old_name, name=None, key=None, is_active=None):
        '''Позволяет редактировать учетную запись.'''

        data = []

        if name:
            data.append(name)

        if key:
            data.append(key)

        if is_active:
            data.append(1 if is_active else 0)

        data.append(old_name)

        n = '?' if name else 'name'
        k = '?' if key else 'key'
        a = '?' if is_active else 'is_active'

        msg = f'''update Login \
                  set name = {n}, key = {k}, is_active = {a} \
                  where name = ?'''

        return self._query(msg, data)

    # === Данные клиентов ===
    def add_user_data(self, name, req):
        '''Распознает тип и данные сообщения и записывает их.'''

        tp = self.exprs['Type'].findall(req)[0]

        if tp == 'cpu':
            msg = 'insert into CPU values(?, ?, ?)'
            data = [name] + self.exprs['CPU'].findall(req) + [dt.now()]

            return self._query(msg, data)

        elif tp == 'ram':
            msg = 'insert into RAM values(?, ?, ?, ?, ?)'
            t1 = [name]
            t2 = list(self.exprs['RAM'].findall(req)[0])
            t3 = [dt.now()]
            data = t1 + t2 + t3

            return self._query(msg, data)

        elif tp == 'swp':
            msg = 'insert into Swap values(?, ?, ?, ?, ?)'
            t1 = [name]
            t2 = list(self.exprs['Swap'].findall(req)[0])
            t3 = [dt.now()]
            data = t1 + t2 + t3

            return self._query(msg, data)

        elif tp == 'dsk':
            msg = 'insert into Disk values(?, ?, ?, ?, ?, ?)'
            t1 = [name]
            t2 = list(self.exprs['Disk'].findall(req)[0])
            t3 = [dt.now()]
            data = t1 + t2 + t3

            return self._query(msg, data)

        else:
            return TypeError('Тип не распознан')

    def get_user_data(self, name, tp, d_from=None, d_to=None):
        '''Ищет записи по имени, типу данных и датам.'''

        if not d_from:
            d_from = '1000-01-01 00:00:00.000000'

        if not d_to:
            d_to = '3000-01-01 00:00:00.000000'

        msg = f'select * from {tp} where name = ? and date > ? and date < ?'
        data = [name, d_from, d_to]

        return self._query(msg, data)

    def del_user_data(self, name, tp, d_from=None, d_to=None):
        '''Удаляет записи по имени, типу данных и датам.'''

        if not d_from:
            d_from = '1000-01-01 00:00:00.000000'

        if not d_to:
            d_to = '3000-01-01 00:00:00.000000'

        msg = f'delete from {tp} where name = ? and date > ? and date < ?'
        data = [name, d_from, d_to]

        return self._query(msg, data)
