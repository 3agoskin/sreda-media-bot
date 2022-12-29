import logging
from aiogram import Bot, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import Dispatcher

from config import TOKEN
from app.dialogs import msg
from database import database as db

# стандартный код создания бота
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())


@dp.message_handler()
async def test_message(message: types.Message):
    # имя юзера из настроек телеграма
    user_name = message.from_user.first_name
    await message.answer(msg.test.format(name=user_name))


async def on_shutdown(dp):
    logging.warning('Shutting down..')
    # закрытие соединения с БД
    db._conn.close()
    logging.warning("DB Connection closed")
