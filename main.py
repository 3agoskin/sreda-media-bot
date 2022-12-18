import logging
import os

from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from middlewares import OfferMiddleware
from survey import create_survey_instance


logging.basicConfig(filename='logename',
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)


API_TOKEN = os.getenv("TG_BOT_API_TOKEN")
OFFER_USERNAME = os.getenv("TG_BOT_OFFER_USERNAME")

bot = Bot(token=API_TOKEN)

storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(OfferMiddleware(OFFER_USERNAME))


@dp.message_handler()
async def send_welcome_message(message: types.Message):
    """Отвечает на любое сообщение перевертышем"""
    args = message.get_args()
    print(f"{args=}")
    text_msg = message.text
    print(text_msg) 
    # задача 2 - логгирование
    logging.info(f"{message.from_user.id} - {text_msg}")
    # задача 3 - сохранение в бд
    survey_instance = create_survey_instance(message)
    await message.answer(f"""
Время: {survey_instance.created}
Ваш ID: {survey_instance.tg_user_id}
Ваш username: {survey_instance.tg_username}
Ваше сообщение: {survey_instance.raw_text}""")



if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)