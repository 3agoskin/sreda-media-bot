import logging
import re

from aiogram import Bot, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.filters import CommandStart

from config import TOKEN
from app.dialogs import msg
from database import database as db

# стандартный код создания бота
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())


@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    """Обработка команды start. Вывод текста и меню"""
    ...


@dp.callback_query_handler(lambda c: c.data == 'main_window')
async def show_main_window(callback_query: types.CallbackQuery):
    """Главный экран"""
    ...






# @dp.message_handler()
# async def test_message(message: types.Message):
#     # имя юзера из настроек телеграма
#     print(message.get_args())
#     user_name = message.from_user.first_name
#     await message.answer(msg.test.format(name=user_name))


async def on_shutdown(dp):
    logging.warning('Shutting down..')
    # закрытие соединения с БД
    db._conn.close()
    logging.warning("DB Connection closed")
