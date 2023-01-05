
import asyncio
import logging
import sqlite3 as sql

import aiogram.utils.markdown as md
from aiogram import Bot, Dispatcher, types
from aiogram.utils import exceptions, executor

from config import TOKEN, WEEK
from database import database as db, cache

API_TOKEN = TOKEN

logging.basicConfig(level=logging.INFO)
log = logging.getLogger('broadcast')

bot = Bot(token=API_TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)


async def get_users():

    #достаем из старой базы 
    conn=sql.connect('survey_new_year_tree.db')
    cursor = conn.cursor()
    cursor.execute("select distinct tg_user_id from survey_new_year_tree")
    records = cursor.fetchall()
    cursor.close()

    #делаем распоковку данные и записываем их в спсок
    users_list = list()
    for user in records:
        user_tg_id, = user
        users_list.append(user_tg_id)
    return users_list


async def send_message(user_id: int, disable_notification: bool = False) -> bool:
    """
    Safe messages sender
    :param user_id:
    :param disable_notification:
    :return:
    """

    text = 'Мы готовили отчёт для вас, поэтому нам важна ваша оценка!\n\nПонравился отчёт?'


    media_report = types.MediaGroup()
    media_report.attach_photo(
        photo = types.InputFile('survey_new_year_tree_report/post1.png'),
        caption='Недавно вы прошли наш первый опрос. Публикуем результаты!')
    media_report.attach_photo(types.InputFile('survey_new_year_tree_report/post2.png'))
    media_report.attach_photo(types.InputFile('survey_new_year_tree_report/post3.png'))
    media_report.attach_photo(types.InputFile('survey_new_year_tree_report/post4.png'))
    media_report.attach_photo(types.InputFile('survey_new_year_tree_report/post5.png'))
    media_report.attach_photo(types.InputFile('survey_new_year_tree_report/post6.png'))
    media_report.attach_photo(types.InputFile('survey_new_year_tree_report/post7.png'))
    media_report.attach_photo(types.InputFile('survey_new_year_tree_report/post8.png'))
    media_report.attach_photo(types.InputFile('survey_new_year_tree_report/post9.png'))





    try:
        await bot.send_media_group(
            chat_id=user_id,
            media=media_report
        )
        msg = await bot.send_message(
        user_id, 
        text, 
        disable_notification=disable_notification,
        reply_markup=types.InlineKeyboardMarkup()\
            .row(types.InlineKeyboardButton('Понравился', callback_data='report_like'))\
            .row(types.InlineKeyboardButton('Не понравился', callback_data='report_dislike'))
        )
        cache.setex(f"msg_survey_new_year_tree_report_{user_id}", WEEK, msg.message_id)
        
    except exceptions.BotBlocked:
        log.error(f"Target [ID:{user_id}]: blocked by user")
    except exceptions.ChatNotFound:
        log.error(f"Target [ID:{user_id}]: invalid user ID")
    except exceptions.RetryAfter as e:
        log.error(f"Target [ID:{user_id}]: Flood limit is exceeded. Sleep {e.timeout} seconds.")
        await asyncio.sleep(e.timeout)
        return await send_message(user_id, text)  # Recursive call
    except exceptions.UserDeactivated:
        log.error(f"Target [ID:{user_id}]: user is deactivated")
    except exceptions.TelegramAPIError:
        log.exception(f"Target [ID:{user_id}]: failed")
    else:
        log.info(f"Target [ID:{user_id}]: success")
        return True
    return False


async def broadcaster() -> int:
    """
    Simple broadcaster
    :return: Count of messages
    """
    count = 0
    try:
        for user_id in await get_users():






            if await send_message(user_id):
                    count += 1
            await asyncio.sleep(.05)  # 20 messages per second (Limit: 30 messages per second)
    finally:
        log.info(f"{count} messages successful sent.")

    return count


if __name__ == '__main__':
    # Execute broadcaster
    executor.start(dp, broadcaster())