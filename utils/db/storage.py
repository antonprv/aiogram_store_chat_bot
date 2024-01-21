from typing import List, Tuple
from sqlite3 import connect


class DatabaseManager:
    '''
    Класс-менеджер базы данных. Умеет отправлять SQL запросы,
    выдавать ответы, создавать таблицы по умолчанию.
    '''
    # При создании объекта класса, подключаемся к БД, разрешаем
    # использование перекрёстных ключей (загон кокретно sqlite3).
    def __init__(self, path: str) -> None:
        self.connect = connect(path)
        self.connect.execute('PRAGMA foreign_keys = on')
        self.connect.commit()
        self.cursor = self.connect.cursor()

    # Создаём необходимые таблицы с помощью вспомогательного метода query.
    # В заказах и тележке cid = уникальный id чата, где заказывается товар.
    def create_tables(self) -> None:
        self.query(
            'CREATE TABLE IF NOT EXISTS products (idx TEXT, title TEXT, '
            'body TEXT, photo BLOB, price INT, tag TEXT)')
        self.query(
            'CREATE TABLE IF NOT EXISTS orders (cid INT, ord_id TEXT,'
            ' state TEXT,'
            'usr_name TEXT, usr_address TEXT, products TEXT)')
        self.query(
            'CREATE TABLE IF NOT EXISTS cart (cid INT, idx TEXT, '
            'quantity INT)')
        self.query(
            'CREATE TABLE IF NOT EXISTS categories (idx TEXT, title TEXT)')
        # Запрос для QIWI-кошелька, пока что не нужен.
        # self.query(
            # 'CREATE TABLE IF NOT EXISTS wallet (cid INT, balance REAL)')
        self.query(
            'CREATE TABLE IF NOT EXISTS questions (cid INT, qid TEXT,'
            ' question TEXT, answer TEXT)')

    # Вспомогательный метод для упрощения SQL-запросов.
    def query(self, argument: str, values: str = None) -> None:
        if values is None:
            self.cursor.execute(argument)
        else:
            self.cursor.execute(argument, values)
        self.connect.commit()

    # Возвращает список с 1 кортежем, в котором 1 строка SQL-ответа.
    def fetchone(self, argument, values=None) -> List[Tuple[str]]:
        if values is None:
            self.cursor.execute(argument) 
        else:
            self.cursor.execute(argument, values)
        return self.cursor.fetchone()

    # Возвращает список со всеми кортежами, все строки SQL-ответа.
    def fetchall(self, argument, values=None) -> List[Tuple[str]]:
        if values is None:
            self.cursor.execute(argument)
        else:
            self.cursor.execute(argument, values)
        return self.cursor.fetchall()

    # Закрываем подключение к БД, когда класс уничтожает сборщик мусора.
    def __del__(self):
        self.connect.close()
