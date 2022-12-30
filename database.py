import os
import logging
import datetime
import sqlite3
import redis
import pytz

import config


# класс наследуется от redis.StrictRedis
class Cache(redis.StrictRedis):
    def __init__(self, host, port, password,
                 charset="utf-8",
                 decode_responses=True):
        super(Cache, self).__init__(host, port,
                                    password=password,
                                    charset=charset,
                                    decode_responses=decode_responses)
        logging.info("Redis start")

   

class Database:
    """ Класс работы с базой данных """
    def __init__(self, name):
        self.name = name
        self._conn = self.connection()
        logging.info("Database connection established")

    def create_db(self):
        connection = sqlite3.connect(f"{self.name}.db")
        logging.info("Database created")
        cursor = connection.cursor()
        with open("createdb.sql", "r") as f:
            sql = f.read()
        cursor.executescript(sql)
        connection.commit()
        cursor.close()

    def connection(self):
        db_path = os.path.join(os.getcwd(), f"{self.name}.db")
        if not os.path.exists(db_path):
            self.create_db()
        return sqlite3.connect(f"{self.name}.db")

    def _execute_query(self, query, select=False):
        cursor = self._conn.cursor()
        cursor.execute(query)
        if select:
            records = cursor.fetchone()
            cursor.close()
            return records
        else:
            self._conn.commit()
        cursor.close()

    async def insert_start_user_and_source(self, tg_user_id: int, tg_username: str, come_from: str):
        created = self._get_now_formatted()
        insert_query = f"""INSERT INTO command_start (created, tg_user_id, tg_username, come_from)
                           VALUES ("{created}", {tg_user_id}, "{tg_username}", "{come_from}")"""
        self._execute_query(insert_query)
        logging.info(f"Start user {tg_user_id} from {come_from} added")

    async def select_users(self, user_id: int):
        select_query = f"""SELECT leagues from users 
                           where id = {user_id}"""
        record = self._execute_query(select_query, select=True)
        return record

    async def update_users(self, user_id: int, leagues: str):
        update_query = f"""Update users 
                              set leagues = "{leagues}" where id = {user_id}"""
        self._execute_query(update_query)
        logging.info(f"Leagues for user {user_id} updated")

    async def delete_users(self, user_id: int):
        delete_query = f"""DELETE FROM users WHERE id = {user_id}"""
        self._execute_query(delete_query)
        logging.info(f"User {user_id} deleted")

    async def insert_or_update_users(self, user_id: int, leagues: str):
        user_leagues = await self.select_users(user_id)
        if user_leagues is not None:
            await self.update_users(user_id, leagues)
        else:
            await self.insert_users(user_id, leagues)

    def _get_now_datetime(self) -> datetime.datetime:
        """Возвращает сег. datetime с учетом временной зоны Мск."""
        tz = pytz.timezone("Europe/Moscow")
        now = datetime.datetime.now(tz)
        return now

    def _get_now_formatted(self) -> str:
        """Возвращает сегоднящнюю дату строкой"""
        return self._get_now_datetime().strftime("%Y-%m-%d %H:%M:%S")

# создание объектов cache и database
cache = Cache(
    host=config.REDIS_HOST,
    port=config.REDIS_PORT,
    password=config.REDIS_PASSWORD
)
database = Database(config.BOT_DB_NAME)
