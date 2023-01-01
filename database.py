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

    async def insert_start_user_and_source(self, tg_user_id: int, tg_username: str, tg_firstname:str, come_from: str):
        created = self._get_now_formatted()
        insert_query = f"""INSERT INTO command_start (created, tg_user_id, tg_username, tg_firstname, come_from)
                           VALUES ("{created}", {tg_user_id}, "{tg_username}", "{tg_firstname}", "{come_from}")"""
        self._execute_query(insert_query)
        logging.info(f"Start user {tg_user_id} from {come_from} added")
    
    async def insert_survey_result(self, tg_user_id: int, city: str, witch_tree: str, why_this_choise:str, where_bought:str, when_bought:str, which_eco: str, why_eco: str, result_survey: str, result_survey_opinion: str, user_phone:str):
        created = self._get_now_formatted()
        insert_query = f"""INSERT INTO survey_new_year_tree (created, tg_user_id, city, witch_tree, why_this_choise, where_bought, when_bought, which_eco, why_eco, result_survey, result_survey_opinion, user_phone)
                           VALUES ("{created}", {tg_user_id}, "{city}", "{witch_tree}", "{why_this_choise}", "{where_bought}", "{when_bought}", "{which_eco}", "{why_eco}", "{result_survey}", "{result_survey_opinion}", "{user_phone}")"""
        self._execute_query(insert_query)
        logging.info(f"Survey result {tg_user_id} added")
    
    async def insert_santa(self, from_tg_user_id: int, to_tg_user_id: int, from_tg_user_username: str, from_tg_user_name:str, postcard_text:str, show_author:bool):
        insert_query = f"""INSERT INTO postcard (from_tg_user_id, to_tg_user_id, from_tg_user_username, from_tg_user_name, postcard_text, show_author, send)
                           VALUES ({from_tg_user_id}, {to_tg_user_id}, "{from_tg_user_username}", "{from_tg_user_name}", "{postcard_text}", "{show_author}", "False")"""
        self._execute_query(insert_query)
        logging.info(f"Santa from {from_tg_user_id} to {to_tg_user_id} added")


    async def select_user_from_command_start(self, tg_user_id: int):
        select_query = f"""SELECT tg_firstname from command_start
                           where tg_user_id = {tg_user_id}"""
        record = self._execute_query(select_query, select=True)
        return record

    async def select_user_from_survey_new_year_tree(self, tg_user_id: int):
        select_query = f"""SELECT id from survey_new_year_tree
                           where tg_user_id = {tg_user_id}"""
        record = self._execute_query(select_query, select=True)
        return record


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
