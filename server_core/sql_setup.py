'''Набор необходимых параметров'''

import re
from dataclasses import dataclass


@dataclass
class Setup:
    '''Пресеты'''

    # Регулярные выражения
    re_login: re.Pattern = re.compile(
        r'name:([a-zA-Zа-яА-Я0-9_]+) ' +
        r'key:([a-zA-Zа-яА-Я0-9_!@#$%^&*()\[\]{}]+)'
    )

    re_cpu: re.Pattern = re.compile(r'type:cpu prc:([0-9]+)')

    re_ram: re.Pattern = re.compile(r'type:ram ttl:([0-9]+) avl:([0-9]+) ' +
                                    r'prc:([0-9]+)')

    re_swap: re.Pattern = re.compile(r'type:swp ttl:([0-9]+) free:([0-9]+) ' +
                                     r'prc:([0-9]+)')

    re_disk: re.Pattern = re.compile(r'type:dsk ltr:([a-z]) ttl:([0-9]+) ' +
                                     r'free:([0-9]+) prc:([0-9]+)')

    re_type: re.Pattern = re.compile(r'type:([a-z]+)')

    # Код для создания базы данных
    sql_login: str = '''CREATE TABLE "Login" (
                    "name" TEXT NOT NULL,
                    "key" TEXT NOT NULL,
                    "is_active" INTEGER CHECK(
                        is_active = 0 or
                        is_active = 1
                        ),
                    PRIMARY KEY("name"))'''

    sql_cpu: str = '''CREATE TABLE "CPU" (
                    "name" TEXT NOT NULL,
                    "prc" INTEGER NOT NULL CHECK(prc>=0 and prc<=100),
                    "date" TEXT NOT NULL,
                    FOREIGN KEY("name") REFERENCES "Login"("name")
                        ON DELETE CASCADE)'''

    sql_ram: str = '''CREATE TABLE "RAM" (
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

    sql_swap: str = '''CREATE TABLE "Swap" (
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

    sql_disk: str = '''CREATE TABLE "Disk" (
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
