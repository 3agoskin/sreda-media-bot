import datetime
from typing import List, NamedTuple, Optional

from aiogram import types
import pytz

from db import insert

class Survey(NamedTuple):
    """Структура добавленного в DB нового опроса"""
    created: str
    tg_user_id: int
    tg_username: Optional[int]
    raw_text: str 

def add_survey(survey_instance: Survey):
    """Добавляет новую запись в DB
    На вход принимает структуру опроса"""
    insert("survey", {
        "created": survey_instance.created,
        "tg_user_id": survey_instance.tg_user_id,
        "tg_username": survey_instance.tg_username,
        "raw_text": survey_instance.raw_text
    })

def create_survey_instance(message: types.Message) -> Survey:
    created = _get_now_formatted()
    tg_user_id = message.from_user.id
    tg_username = message.from_user.username
    raw_text = message.text
    survey_instance = Survey(created, tg_user_id, tg_username, raw_text)
    add_survey(survey_instance)
    return survey_instance

def _get_now_formatted() -> str:
    """Возвращает сегоднящнюю дату строкой"""
    return _get_now_datetime().strftime("%Y-%m-%d %H:%M:%S")

def _get_now_datetime() -> datetime.datetime:
    """Возвращает сег. datetime с учетом временной зоны Мск."""
    tz = pytz.timezone("Europe/Moscow")
    now = datetime.datetime.now(tz)
    return now