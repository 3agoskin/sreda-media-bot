import logging
import re

from aiogram import Bot, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.filters import CommandStart

from config import TOKEN, WEEK
from app.dialogs import msg
from database import database as db, cache
import app.service as s

# стандартный код создания бота
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())


@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    """Обработка команды start. Предложение начать опрос"""
    offer_subscribe = await s.bot_start(message)
    if offer_subscribe:
        await message.answer(msg.ref_text.format(name=message.from_user.first_name))
    msg_survey = await message.answer(
        msg.survey_offer, 
        parse_mode=types.ParseMode.MARKDOWN_V2,
        reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton('Погнали к опросу', callback_data='survey_start')))
    cache.setex(f"survey_msg_to_{message.from_user.id}", WEEK, msg_survey.message_id)
    


@dp.callback_query_handler(lambda c: c.data == 'survey_start')
async def survey_step1(callback_query: types.CallbackQuery):
#     """Главный экран"""
    await bot.edit_message_text(
        text=msg.survey_step1_where_are_you_from,
        chat_id=callback_query.from_user.id,
        message_id=cache.get(f"survey_msg_to_{callback_query.from_user.id}"),
        reply_markup=InlineKeyboardMarkup()\
            .row(InlineKeyboardButton("Ханты-Мансийск", callback_data='survey_step1_hm'))\
            .row(InlineKeyboardButton("Другой город", callback_data='survey_step1_anothercity')))

@dp.callback_query_handler(lambda c: str(c.data).startswith('survey_step1'))
async def survey_step2(callback_query: types.CallbackQuery):
    print('=')
    if callback_query.data.split('_')[-1] == 'anothercity':
        msg_dots = await bot.send_message(text="либо отправить геопозицию (а мы потом поймем откуда вы!)", chat_id=callback_query.from_user.id, reply_markup=ReplyKeyboardMarkup().add(KeyboardButton('Отправить свою геопозицию', request_location=True))
        )
        cache.setex(f"geo_msg_for_{callback_query.from_user.id}", WEEK, msg_dots.message_id)
        await bot.edit_message_text(
            text=msg.survey_step1_anothercity,
            chat_id=callback_query.from_user.id,
            message_id=cache.get(f"survey_msg_to_{callback_query.from_user.id}"),
            reply_markup=InlineKeyboardMarkup()\
                .row(InlineKeyboardButton("Извините, я все же из Ханты-Мансийска", callback_data='survey_step1_hm'))
        )
    






# @dp.message_handler()
# async def test_message(message: types.Message):
#     # имя юзера из настроек телеграма
#     print(message.get_args())
#     user_name = message.from_user.first_name
#     await message.answer(msg.test.format(name=user_name)) # охуенно! 


async def on_shutdown(dp):
    logging.warning('Shutting down..')
    # закрытие соединения с БД
    db._conn.close()
    logging.warning("DB Connection closed")
