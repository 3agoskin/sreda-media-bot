import logging
import os

import aiogram.utils.markdown as md
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup

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

#до Redis используем локальную память
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(OfferMiddleware(OFFER_USERNAME))


# States
class Form(StatesGroup):
    name = State()  
    age = State()  
    gender = State() 



@dp.message_handler()
async def send_welcome_message(message: types.Message):
    """
    Начало общения с ботом
    """
    args = message.get_args()
    print(f"{args=}")
    text_msg = message.text
    print(text_msg) 

    # задача 2 - логгирование
    logging.info(f"{message.from_user.id} - {text_msg}")

    # задача 3 - сохранение в бд
    survey_instance = create_survey_instance(message)

    # задача 4 - сохранение состояния
    if text_msg == 'состояние':
        await Form.name.set()
        await message.answer('Состояние установлено')
        return


    await message.answer(
        md.text(
            md.text("Время:", md.italic(survey_instance.created)),
            md.text("Ваш ID:", md.italic(survey_instance.tg_user_id)),
            md.text("Ваш username:", md.bold(survey_instance.tg_username)),
            md.text("Ваше сообщение:", md.code(survey_instance.raw_text)),
            sep="\n"
        ),
        parse_mode=types.ParseMode.MARKDOWN_V2
        )


@dp.message_handler(state=Form.name)
@dp.message_handler()
async def process_name(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer('Финиш')





if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)