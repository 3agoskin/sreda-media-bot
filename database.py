import os
import logging
import datetime
import sqlite3
import redis
import pytz
import csv

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

    def _execute_query(self, query, select=False, fetchone=True):
        cursor = self._conn.cursor()
        cursor.execute(query)
        if select and fetchone:
            records = cursor.fetchone()
            cursor.close()
            return records
        elif select and not fetchone:
            records = cursor.fetchall()
            cursor.close()
            return records
        else:
            self._conn.commit()
        cursor.close()



    async def insert_command_start_user_and_source(self, tg_user_id: int, come_from: str):
        created = self._get_now_formatted()
        insert_query = f"""INSERT INTO command_start (created, tg_user_id, come_from)
                           VALUES ("{created}", {tg_user_id}, "{come_from}")"""
        self._execute_query(insert_query)
        logging.info(f"Start user {tg_user_id} from {come_from} added")

    async def insert_survey_new_year_tree_total(self, tg_user_id: int, liked: bool, share: bool = None, reason_dislike: str = None):
        created = self._get_now_formatted()
        insert_query = f"""INSERT INTO survey_new_year_tree_total (created, tg_user_id, liked, share, reason_dislike)
                           VALUES ("{created}", {tg_user_id}, "{liked}", "{share}", "{reason_dislike}")"""
        self._execute_query(insert_query)
        logging.info(f"Survey_new_year_tree_total user {tg_user_id} added")
    
    async def update_survey_new_year_tree_total(self, tg_user_id: int, name_row:str, value_row:str):
        update_query = f'''UPDATE survey_new_year_tree_total SET {name_row}="{value_row}"
                            WHERE tg_user_id={tg_user_id}'''
        self._execute_query(update_query)



    # async def get_data(self) -> str:
    #     logging.info("Exporting data into CSV............")
    #     select_query = '''SELECT * FROM survey_new_year_tree;'''
    #     cursor = self._conn.cursor()
    #     cursor.execute(select_query)

    #     with open("survey_new_year_tree.csv", "w") as csv_file:
    #         csv_writer = csv.writer(csv_file, dialect='excel')
    #         csv_writer.writerow([i[0] for i in cursor.description])
    #         csv_writer.writerows(cursor)
        
    #     dirpath = os.getcwd() + "/survey_new_year_tree.csv"
    #     logging.info("Data exported Successfully into {}".format(dirpath))
    #     return "survey_new_year_tree.csv"


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
