import asyncio
import logging

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
    all_users_list = await db.select_all_users_from_command_start()
    users_list = list()
    for user in all_users_list:
        user_tg_id, = user
        if not cache.get(f'user_phone_{user_tg_id}') and not cache.get(f'complete_survey_sending_{user_tg_id}'):
            users_list.append(user_tg_id)
            cache.setex(f'complete_survey_sending_{user_tg_id}', WEEK, 'True')
    print(users_list)
    return users_list


async def send_message(user_id: int, text: str, disable_notification: bool = False) -> bool:
    """
    Safe messages sender
    :param user_id:
    :param text:
    :param disable_notification:
    :return:
    """
    try:
        await bot.send_message(
        user_id, 
        text, 
        disable_notification=disable_notification)
        
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



            text_to_user = """Добрый день!

Вы недавно запустили бота «Среды», но не прошли опрос до конца. Пожалуйста, завершите его, нам важен каждый человек! 

Опрос можно будет пройти до середины среды, а завтра вечером мы опубликуем результаты. 
____

Возможно вы остановились на одном из этих этапов:

1. Написать мнение, какая елка экологичнее. Если не хотите писать, пропустите, нажав /start

2. Написать отзыв про опрос. Пропустить этот пункт можно так же нажав /start

3. Финальный вопрос – укажите вашу OS на телефоне: iOS или Android, чтобы бот выдал вам нужную инструкцию и записал ваши ответы.

Начать опрос заново – /start"""



            if await send_message(user_id, text_to_user):
                    count += 1
            await asyncio.sleep(.05)  # 20 messages per second (Limit: 30 messages per second)
    finally:
        log.info(f"{count} messages successful sent.")

    return count


if __name__ == '__main__':
    # Execute broadcaster
    executor.start(dp, broadcaster())