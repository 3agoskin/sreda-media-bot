import logging
import re
import asyncio

import aiogram.utils.markdown as md
from aiogram import Bot, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.dispatcher.filters import CommandStart
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils.deep_linking import get_start_link, decode_payload

import config
from config import TOKEN, WEEK
from app.dialogs import msg
from database import database as db, cache
import app.service as s


# стандартный код создания бота
bot = Bot(token=TOKEN)

storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)



class Form(StatesGroup):
    santa = State()
    geo = State()
    eco = State()
    feedback = State()



# @dp.message_handler(commands=['data'])
# async def data (message: types.Message):
#     path_file = await db.get_data()
#     await bot.send_document(
#         chat_id=message.from_user.id,
#         document=types.InputFile(
#             path_or_bytesio=path_file,
#             filename='survey_new_year_tree.csv'),
#         caption='Данные с опроса по ёлка в csv формате'
#         )
        

@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message, state: FSMContext):
    tg_user_id = message.from_user.id
    deep_link = message.get_args()


    match deep_link:
        case "":
            await db.insert_command_start_user_and_source(tg_user_id, '/start')
        case _:
            come_from = decode_payload(deep_link)
            await db.insert_command_start_user_and_source(tg_user_id, come_from)
    
    await bot.send_message(
        chat_id = message.from_user.id, 
        text=md.text(
            md.bold('Скоро будут новые опросы, но пока не пропустите новые публикации, подписывайтесь на нас в соцсетях:'),
            md.text('▪️ ' ,md.link('Инстаграм', 'https://www.instagram.com/sreda_media/'), "\*", sep=''),
            md.text('▪️', md.link('Телеграм', 'https://t.me/SredaMediaChannel')),
            md.text('▪️', md.link('ВК', 'https://vk.com/sredamediapublic')),
            md.text(),
            md.text('\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_'),
            md.italic('*принадлежит Meta,\nпризнанной экстремистской в России'),
            sep='\n'
        ), 
        parse_mode=types.ParseMode.MARKDOWN_V2,
        disable_web_page_preview=True)


@dp.callback_query_handler(lambda c: str(c.data).startswith('report'))
async def report(callback_query: types.CallbackQuery):
    parametr = callback_query.data.split('_')[-1]
    user_id = callback_query.from_user.id
    message_id=cache.get(f"msg_survey_new_year_tree_report_{user_id}")
    match parametr:
        case 'like':
            await db.insert_survey_new_year_tree_total(user_id, True)
            await bot.edit_message_text(
                text='Это здорово, мы старались!\nИ еще один вопрос: вы готовы поделиться результатом с друзьями?',
                chat_id=user_id,
                message_id=message_id,
                reply_markup=InlineKeyboardMarkup()\
                    .row(InlineKeyboardButton(text="Поделюсь", callback_data='report_share'))\
                    .row(InlineKeyboardButton(text="Не хочу", callback_data='report_notshare'))
            )
        case 'dislike':
            await db.insert_survey_new_year_tree_total(user_id, False)
            await bot.edit_message_text(
                text='Очень жаль, потому что мы старались!\nНо это наш первый отчет и он неидеальный. Расскажите нам: почему вам отчет не понравился?',
                chat_id=user_id,
                message_id=message_id,
                reply_markup=InlineKeyboardMarkup()\
                    .row(InlineKeyboardButton(text="Маленькая выборка", callback_data='report_smallselection'))\
                    .row(InlineKeyboardButton(text="Не нравится визуализация", callback_data='report_badvisualization'))\
                    .row(InlineKeyboardButton(text="Непонятный отчёт", callback_data='report_incomprehensiblereport'))\
            )
        case 'share':
            user_deep_link = await get_start_link(user_id, encode=True)
            await db.update_survey_new_year_tree_total(user_id, 'share', True)
            await bot.edit_message_text(
                text='Хорошо, вот тогда вам сообщение, что вы прошли опрос, можете его и картинки выше отпраивть другу. Спасибо за участие!',
                chat_id=user_id,
                message_id=message_id,
                reply_markup=InlineKeyboardMarkup()
            )
            await bot.send_message(
                chat_id=user_id,
                text=md.text(
                    md.bold('Мой голос есть в этом опросе от «Среды»'),
                    md.text('▪️ ' ,md.link('Инстаграм', 'https://www.instagram.com/p/CnCT4LPo5Jt/'), "\*", sep=''),
                    md.text('▪️', md.link('Телеграм', 'https://t.me/SredaMediaChannel/75')),
                    md.text('▪️', md.link('ВК', 'https://vk.com/sredamediapublic?w=wall-215394554_48')),
                    md.text(),
                    md.text('▪️ Пройти опрос можно здесь - ', md.link('@SredaMediaBot', user_deep_link)),
                    md.text(),
                    md.text('\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_'),
                    md.italic('*принадлежит Meta,\nпризнанной экстремистской в России'),
                    sep='\n'
                    ), 
                parse_mode=types.ParseMode.MARKDOWN_V2,
                )
        case 'notshare':
            await db.update_survey_new_year_tree_total(user_id, 'share', False)
            await bot.edit_message_text(
                text='Хорошо, но вы можете принять участие в будущем опросе «Среды». Спасибо за участие!',
                chat_id=user_id,
                message_id=message_id,
                reply_markup=InlineKeyboardMarkup()
            )
        case 'smallselection':
            await db.update_survey_new_year_tree_total(user_id, 'reason_dislike', parametr)
            await bot.edit_message_text(
                text='Хорошо, мы записали ваш ответ, но вы можете принять участие в будущем опросе «Среды». Спасибо за участие!',
                chat_id=user_id,
                message_id=message_id,
                reply_markup=InlineKeyboardMarkup()
            )
        case 'badvisualization':
            await db.update_survey_new_year_tree_total(user_id, 'reason_dislike', parametr)
            await bot.edit_message_text(
                text='Хорошо, мы записали ваш ответ, но вы можете принять участие в будущем опросе «Среды». Спасибо за участие!',
                chat_id=user_id,
                message_id=message_id,
                reply_markup=InlineKeyboardMarkup()
            )
        case 'incomprehensiblereport':
           await db.update_survey_new_year_tree_total(user_id, 'reason_dislike', parametr)
           await bot.edit_message_text(
                text='Хорошо, мы записали ваш ответ, но вы можете принять участие в будущем опросе «Среды». Спасибо за участие!',
                chat_id=user_id,
                message_id=message_id,
                reply_markup=InlineKeyboardMarkup()
            )



async def on_shutdown(dp):
    logging.warning('Shutting down..')
    # закрытие соединения с БД
    db._conn.close()
    logging.warning("DB Connection closed")
