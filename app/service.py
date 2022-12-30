from aiogram import types
from database import database as db

async def bot_start(message: types.Message):
    """Записываем в бд старт, если был реф - отправляем True, чтобы потом в логике бота описать то, чтобы на нас можно еще и подписаться!"""
    tg_user_id = message.from_user.id
    tg_username = message.from_user.username
    deep_link = message.get_args()
    match deep_link:
        case "plastik_or_real_tree":
            await db.insert_start_user_and_source(tg_user_id, tg_username, "inst_about")
        case "story":
            await db.insert_start_user_and_source(tg_user_id, tg_username, "inst_story") 
        case "channel":
            await db.insert_start_user_and_source(tg_user_id, tg_username, "tg_channel") 
        case "public":
            await db.insert_start_user_and_source(tg_user_id, tg_username, "vk_public") 
        case "":
            await db.insert_start_user_and_source(tg_user_id, tg_username, "directly") 
        case _:
            await db.insert_start_user_and_source(tg_user_id, tg_username, message.get_args())
            return True