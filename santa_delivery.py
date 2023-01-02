import asyncio
import logging

import aiogram.utils.markdown as md
from aiogram import Bot, Dispatcher, types
from aiogram.utils import exceptions, executor

from config import TOKEN
from database import database as db

API_TOKEN = TOKEN

logging.basicConfig(level=logging.INFO)
log = logging.getLogger('broadcast')

bot = Bot(token=API_TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)


async def get_users():
    users_list = await db.select_postcard_from_secter_santa()
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
        for user in await get_users():
            id, from_tg_user_id, to_tg_user_id, from_tg_user_username, from_tg_user_name, postcard_text, show_author = user

            print (id, from_tg_user_id, to_tg_user_id, from_tg_user_username, from_tg_user_name, postcard_text, show_author)

            if show_author:
                author = f"""От {from_tg_user_name} @{from_tg_user_username}"""
            else:
                author = 'От анонима...'


            text_to_tg_user_id = f"""
Вам открытка!

{postcard_text}

{author}

_
Спасибо, разместили ссылку и помогли «Среде». С новым годом! 
"""

            text_from_tg_user_id = 'Отправили вашу открытку получателю! Ему или ей точно будет приятно. Спасибо, что дарите добро 💚'

            if await send_message(to_tg_user_id, text_to_tg_user_id):
                if await send_message(from_tg_user_id, text_from_tg_user_id):
                    await db.update_send_poscard(id)
                    count += 1
            await asyncio.sleep(.05)  # 20 messages per second (Limit: 30 messages per second)
    finally:
        log.info(f"{count} messages successful sent.")

    return count


if __name__ == '__main__':
    # Execute broadcaster
    executor.start(dp, broadcaster())