import asyncio

from aiogram import types
from aiogram.utils.deep_linking import get_start_link, decode_payload

from config import WEEK
from app.dialogs import msg
from database import database as db, cache

async def bot_start(message: types.Message):
    """Записываем в бд старт, если был реф - отправляем True, чтобы потом в логике бота описать то, чтобы на нас можно еще и подписаться!"""
    tg_user_id = message.from_user.id
    tg_username = message.from_user.username
    f_name = message.from_user.first_name
    l_name = clear_last_name(message.from_user.last_name)
    tg_firstname = f_name + ' ' + l_name
    deep_link = message.get_args()
    clear_cache(message)
    match deep_link:
        case "plastik_or_real_tree":
            await db.insert_start_user_and_source(tg_user_id, tg_username, tg_firstname, "inst_about")
        case "story":
            await db.insert_start_user_and_source(tg_user_id, tg_username, tg_firstname, "inst_story") 
        case "channel":
            await db.insert_start_user_and_source(tg_user_id, tg_username, tg_firstname, "tg_channel") 
        case "public":
            await db.insert_start_user_and_source(tg_user_id, tg_username, tg_firstname, "vk_public") 
        case "":
            await db.insert_start_user_and_source(tg_user_id, tg_username, tg_firstname, "directly") 
        case _:
            from_who = await _secret_santa(message.get_args())
            await db.insert_start_user_and_source(tg_user_id, tg_username, tg_firstname,  from_who)
            if from_who == None:
                return False
            return from_who


async def clear_keyboard_and_messages(bot, message):
    await bot.delete_message(
        chat_id=message.from_user.id,
        message_id=cache.get(f"geo_msg_for_{message.from_user.id}")
    )
    msg_remove = await bot.send_message(text='...', chat_id=message.from_user.id, reply_markup=types.ReplyKeyboardRemove())
    await bot.delete_message(
        chat_id=message.from_user.id,
        message_id=msg_remove.message_id
    )


async def step2(bot, message: types.Message):
    await bot.delete_message(
        chat_id=message.from_user.id,
        message_id=cache.get(f"survey_msg_to_{message.from_user.id}")
    )
    msg_survey = await bot.send_message(
        text=msg.survey_step2_witchtree,
        chat_id=message.from_user.id,
        reply_markup=types.InlineKeyboardMarkup()\
            .row(types.InlineKeyboardButton('Самая настоящая ёлка! 🌲', callback_data='survey_step2_realtree'))\
            .row(types.InlineKeyboardButton('Самая ненастоящая (искусственная)! 🎄', callback_data='survey_step2_plastictree'))\
            .row(types.InlineKeyboardButton('Нет дома ёлки ❌', callback_data='survey_step2_nonetree'))
    )
    await asyncio.sleep(2)
    cache.setex(f"survey_msg_to_{message.from_user.id}", WEEK, msg_survey.message_id)

async def else_where_did_buy_tree(bot, callback_query, step=4):
    await bot.edit_message_text(
                    text=msg.survey_step4_where_did_you_buy_tree,
                    chat_id=callback_query.from_user.id,
                    message_id=cache.get(f'survey_msg_to_{callback_query.from_user.id}'),
                    reply_markup=types.InlineKeyboardMarkup()\
                        .row(types.InlineKeyboardButton(text='В своем городе', callback_data=f'survey_step{step}_inCity'))\
                        .row(types.InlineKeyboardButton(text='В другом городе', callback_data=f'survey_step{step}_notInThisCity'))\
                        .row(types.InlineKeyboardButton(text='Не хочу указывать', callback_data=f'survey_step{step}_noneData'))\
                )


async def witch_tree_more_eco(bot, callback_query):
    await bot.edit_message_text(
                    text=msg.survey_step6,
                    chat_id=callback_query.from_user.id,
                    message_id=cache.get(f'survey_msg_to_{callback_query.from_user.id}'),
                    reply_markup=types.InlineKeyboardMarkup()\
                        .row(types.InlineKeyboardButton(text='Живая 🌲', callback_data=f'survey_step6_real'))\
                        .row(types.InlineKeyboardButton(text='Искусственная 🎄', callback_data=f'survey_step6_plastic'))\
                        .row(types.InlineKeyboardButton(text='Никакая ❌', callback_data=f'survey_step6_notAny'))\
                )

async def _secret_santa(deeplink):
    payload = int(decode_payload(deeplink))
    to_name = await db.select_user_from_command_start(payload)
    return to_name, payload






def clear_cache(message):
    city = cache.setex(f"result_city_{message.from_user.id}", WEEK, '')
    tree = cache.setex(f"result_tree_{message.from_user.id}", WEEK, '')
    reason_tree = cache.setex(f"result_reason_{message.from_user.id}", WEEK, '')
    where_did_buy = cache.setex(f"result_where_did_buy_{message.from_user.id}", WEEK, '')
    when_did_buy = cache.setex(f"result_when_did_buy_{message.from_user.id}", WEEK, '')
    opinion_eco = cache.setex(f"result_opinion_eco_tree_{message.from_user.id}", WEEK, '')
    open_pinion_eco = cache.setex(f"result_open_opinion_eco_tree_{message.from_user.id}", WEEK, '')
    result_survey = cache.setex(f"result_survey_{message.from_user.id}", WEEK, '')
    result_survey_opinion = cache.setex(f"result_survey_opinion_{message.from_user.id}", WEEK, '')

def clear_last_name(l_name):
    l_name = str(l_name)
    if l_name == 'None':
        return ''
    return l_name