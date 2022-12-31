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
dp.middleware.setup(LoggingMiddleware())


class Form(StatesGroup):
    santa = State()
    geo = State()
    eco = State()
    feedback = State()


@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message, state: FSMContext):
    """Обработка команды start. Предложение начать опрос"""
    santa_secret = await s.bot_start(message)
    print(f"{santa_secret=}")
    if santa_secret:
        santa_secret, to_id = santa_secret
        santa_secret, = santa_secret
        await Form.santa.set()
        cache.setex(f"santa_to_{message.from_user.id}", WEEK, to_id)
        await message.answer(msg.ref_text.format(name=santa_secret))
    else:
        state.finish()
        msg_survey = await message.answer(
            msg.survey_offer, 
            parse_mode=types.ParseMode.MARKDOWN_V2,
            reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton('Погнали к опросу', callback_data='survey_start')))
        cache.setex(f"survey_msg_to_{message.from_user.id}", WEEK, msg_survey.message_id)
    



@dp.message_handler(content_types=['text'], state=Form.santa)
async def secret_santa(message: types.Message, state: FSMContext):
    cache.setex(f"santa_{message.from_user.id}", WEEK, message.text)
    await bot.send_message(
        chat_id=message.from_user.id,
        text='Анонимно или напрямую?',
        reply_markup=InlineKeyboardMarkup().row(InlineKeyboardButton("🦸🏻‍♀️🦸🏼‍♂️ анонимно", callback_data='santa_secret'))\
            .row(InlineKeyboardButton("🤵🏻‍♀️🤵🏼 напрямую", callback_data='santa_open'))
    )

@dp.callback_query_handler(lambda c: str(c.data).startswith('santa'), state=Form.santa)
async def save_santa_text(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    parametr = callback_query.data.split('_')[-1]
    from_id = callback_query.from_user.id
    from_username = callback_query.from_user.username
    from_name = callback_query.from_user.first_name + ' ' + callback_query.from_user.last_name
    to_id = cache.get(f"santa_to_{callback_query.from_user.id}")
    print(f"{to_id=}")
    postcard_text = cache.get(f"santa_{callback_query.from_user.id}")
    match parametr:
        case 'secret':
            await db.insert_santa(
                from_tg_user_id=from_id,
                to_tg_user_id=to_id,
                from_tg_user_username=from_username,
                from_tg_user_name=from_name,
                postcard_text=postcard_text,
                show_author=False
            )
            await bot.send_message(
                chat_id=callback_query.from_user.id,
                text="Отправим анонимно, вас тоже уведомим об отправке\n\nОпрос по ёлкам - /start"
            )
        case 'open':
            await db.insert_santa(
                from_tg_user_id=from_id,
                to_tg_user_id=to_id,
                from_tg_user_username=from_username,
                from_tg_user_name=from_name,
                postcard_text=postcard_text,
                show_author=True
            )
            await bot.send_message(
                chat_id=callback_query.from_user.id,
                text="Отправим с вашим именем, вас тоже уведомим об отправке\n\nОпрос по ёлкам - /start"
            )
    
    








@dp.callback_query_handler(lambda c: c.data == 'survey_start')
async def survey_step1(callback_query: types.CallbackQuery):
    """Обработка кнопки - Погнали к опросу"""
    
    await bot.edit_message_text(
        text=msg.survey_step1_where_are_you_from,
        chat_id=callback_query.from_user.id,
        message_id=cache.get(f"survey_msg_to_{callback_query.from_user.id}"),
        reply_markup=InlineKeyboardMarkup()\
            .row(InlineKeyboardButton("Ханты-Мансийск", callback_data='survey_step1_hm'))\
            .row(InlineKeyboardButton("Другой город", callback_data='survey_step1_anothercity')))

@dp.callback_query_handler(lambda c: str(c.data).startswith('survey_step1'))
async def survey_step2(callback_query: types.CallbackQuery):
    '''Обработка кнопки - другой город'''
    
    if callback_query.data.split('_')[-1] == 'anothercity':
        await Form.geo.set()
        msg_dots = await bot.send_message(
            text="либо отправьте геопозицию (а мы потом поймем откуда вы!)",\
            chat_id=callback_query.from_user.id,\
            reply_markup=ReplyKeyboardMarkup().add(KeyboardButton('Отправить свою геопозицию', request_location=True))
        )
        cache.setex(f"geo_msg_for_{callback_query.from_user.id}", WEEK, msg_dots.message_id)
        await bot.edit_message_text(
            text=msg.survey_step1_anothercity,
            chat_id=callback_query.from_user.id,
            message_id=cache.get(f"survey_msg_to_{callback_query.from_user.id}"),)
        
    else:
        cache.setex(f"result_city_{callback_query.from_user.id}", WEEK, 'hm')
        await s.step2(bot, callback_query)




@dp.message_handler(content_types=['location'], state=Form.geo)
async def get_geo(message: types.Message, state: FSMContext):
    '''обработка геолокации'''
    
    cache.setex(f"result_city_{message.from_user.id}", WEEK, f"{message.location.latitude}, {message.location.longitude}")
    await s.clear_keyboard_and_messages(bot, message)
    await state.finish()
    await s.step2(bot, message)



@dp.message_handler(content_types=['text'], state=Form.geo)
async def get_geo(message: types.Message, state: FSMContext):
    '''обработка текста другого города'''
    
    cache.setex(f"result_city_{message.from_user.id}", WEEK, message.text)
    await s.clear_keyboard_and_messages(bot, message)
    await state.finish()
    await s.step2(bot, message)


@dp.callback_query_handler(lambda c: str(c.data).startswith('survey_step2'))
async def survey_step3(callback_query: types.CallbackQuery):
    
    tree = callback_query.data.split('_')[-1]
    match tree:
        case 'realtree':
            cache.setex(f"result_tree_{callback_query.from_user.id}", WEEK, tree)
            await bot.edit_message_text(
                text=msg.survey_step3_why_real_tree,
                chat_id=callback_query.from_user.id,
                message_id=cache.get(f'survey_msg_to_{callback_query.from_user.id}'),
                reply_markup=InlineKeyboardMarkup()\
                    .row(InlineKeyboardButton(text='Запах!', callback_data='survey_step3_smell'))\
                    .row(InlineKeyboardButton(text='Не надо хранить - удобно!', callback_data='survey_step3_confort'))\
                    .row(InlineKeyboardButton(text='Просто больше нравится', callback_data='survey_step3_like'))\
                    .row(InlineKeyboardButton(text='Приемлемая цена', callback_data='survey_step3_price'))\
            )
        case 'plastictree':
            cache.setex(f"result_tree_{callback_query.from_user.id}", WEEK, tree)
            await bot.edit_message_text(
                text=msg.survey_step3_why_plastic_tree,
                chat_id=callback_query.from_user.id,
                message_id=cache.get(f'survey_msg_to_{callback_query.from_user.id}'),
                reply_markup=InlineKeyboardMarkup()\
                    .row(InlineKeyboardButton(text='Она надолго', callback_data='survey_step3_long'))\
                    .row(InlineKeyboardButton(text='Она намного удобнее', callback_data='survey_step3_comfort'))\
                    .row(InlineKeyboardButton(text='Просто больше нравится', callback_data='survey_step3_like'))\
                    .row(InlineKeyboardButton(text='Приемлемая цена', callback_data='survey_step3_price'))\
            )
        case 'nonetree':
            cache.setex(f"result_tree_{callback_query.from_user.id}", WEEK, tree)
            await bot.edit_message_text(
                text=msg.survey_step3_why_none_tree,
                chat_id=callback_query.from_user.id,
                message_id=cache.get(f'survey_msg_to_{callback_query.from_user.id}'),
                reply_markup=InlineKeyboardMarkup()\
                    .row(InlineKeyboardButton(text='Не отмечаю Новый год совсем', callback_data='survey_step3_nonnewyear'))\
                    .row(InlineKeyboardButton(text='Отмечаю по китай. календарю', callback_data='survey_step3_chineseyear'))\
                    .row(InlineKeyboardButton(text='Нет желания ставить ёлку/нет времени', callback_data='survey_step3_nowish'))\
            )


@dp.callback_query_handler(lambda c: str(c.data).startswith('survey_step3'))
async def survey_step4(callback_query: types.CallbackQuery):
    
    reason = callback_query.data.split('_')[-1]
    match reason:
        case "price":
            cache.setex(f"result_reason_{callback_query.from_user.id}", WEEK, reason)
        case "confort":
            cache.setex(f"result_reason_{callback_query.from_user.id}", WEEK, reason)
        case "like":
            cache.setex(f"result_reason_{callback_query.from_user.id}", WEEK, reason)
        case "long":
            cache.setex(f"result_reason_{callback_query.from_user.id}", WEEK, reason)
        case "smell":
            cache.setex(f"result_reason_{callback_query.from_user.id}", WEEK, reason)
        case "nonnewyear":
            cache.setex(f"result_reason_{callback_query.from_user.id}", WEEK, reason)
        case "chineseyear":
            cache.setex(f"result_reason_{callback_query.from_user.id}", WEEK, reason)
        case "nowish":
            cache.setex(f"result_reason_{callback_query.from_user.id}", WEEK, reason)
    
    tree = cache.get(f"result_tree_{callback_query.from_user.id}")
    match tree:
        case "realtree":
            if cache.get(f"result_city_{callback_query.from_user.id}") == "hm":
                await bot.edit_message_text(
                    text=msg.survey_step4_where_did_you_buy_tree_hm,
                    chat_id=callback_query.from_user.id,
                    message_id=cache.get(f'survey_msg_to_{callback_query.from_user.id}'),
                    reply_markup=InlineKeyboardMarkup()\
                        .row(InlineKeyboardButton(text='Да, прям из списка', callback_data='survey_step4_list'))\
                        .row(InlineKeyboardButton(text='Нет, совсем не из списка', callback_data='survey_step4_notList'))\
                )
            else:
                await s.else_where_did_buy_tree(bot, callback_query)
        case "plastictree":
            await bot.edit_message_text(
                    text=msg.survey_step4_when_did_you_buy_tree,
                    chat_id=callback_query.from_user.id,
                    message_id=cache.get(f'survey_msg_to_{callback_query.from_user.id}'),
                    reply_markup=InlineKeyboardMarkup()\
                        .row(InlineKeyboardButton(text='В этом году', callback_data='survey_step4_thisYear'))\
                        .row(InlineKeyboardButton(text='1-3 года назад', callback_data='survey_step4_1or3YearAgo'))\
                        .row(InlineKeyboardButton(text='4-7 лет назад', callback_data='survey_step4_4or7YearAgo'))\
                        .row(InlineKeyboardButton(text='Больше 7 лет назад', callback_data='survey_step4_more7YearAgo'))\
                )
        case "nonetree":
            await s.witch_tree_more_eco(bot, callback_query)
        

@dp.callback_query_handler(lambda c: str(c.data).startswith('survey_step4'))
async def survey_step4(callback_query: types.CallbackQuery):
    
    parametr = callback_query.data.split('_')[-1]
    match parametr:
        case "list":
            cache.setex(f"result_where_did_buy_{callback_query.from_user.id}", WEEK, parametr)
        case "notList":
            return await s.else_where_did_buy_tree(bot, callback_query)
        case "inCity":
            cache.setex(f"result_where_did_buy_{callback_query.from_user.id}", WEEK, parametr)
        case "notInThisCity":
            cache.setex(f"result_where_did_buy_{callback_query.from_user.id}", WEEK, parametr)
        case "noneData":
            cache.setex(f"result_where_did_buy_{callback_query.from_user.id}", WEEK, parametr)
        case "thisYear":
            cache.setex(f"result_when_did_buy_{callback_query.from_user.id}", WEEK, parametr)
        case "1or3YearAgo":
            cache.setex(f"result_when_did_buy_{callback_query.from_user.id}", WEEK, parametr)
        case "4or7YearAgo":
            cache.setex(f"result_when_did_buy_{callback_query.from_user.id}", WEEK, parametr)
        case "more7YearAgo":
            cache.setex(f"result_when_did_buy_{callback_query.from_user.id}", WEEK, parametr)
        
    tree = cache.get(f"result_tree_{callback_query.from_user.id}")
    match tree:
        case "realtree":
            await bot.edit_message_text(
                    text=msg.survey_step5_when_did_you_buy_tree,
                    chat_id=callback_query.from_user.id,
                    message_id=cache.get(f'survey_msg_to_{callback_query.from_user.id}'),
                    reply_markup=InlineKeyboardMarkup()\
                        .row(InlineKeyboardButton(text='За неделю до нового года', callback_data='survey_step5_4weekDecember'))\
                        .row(InlineKeyboardButton(text='За две недели до нового года', callback_data='survey_step5_3weekDecember'))\
                        .row(InlineKeyboardButton(text='В первой половине декабря', callback_data='survey_step5_firstHalfDecember'))\
                        .row(InlineKeyboardButton(text='Еще в ноябре', callback_data='survey_step5_november'))\
                )
        case "plastictree":
            await s.else_where_did_buy_tree(bot, callback_query, step=5)

@dp.callback_query_handler(lambda c: str(c.data).startswith('survey_step5'))
async def survey_step6(callback_query: types.CallbackQuery):
    
    parametr = callback_query.data.split('_')[-1]
    match parametr:
        case "inCity":
            cache.setex(f"result_where_did_buy_{callback_query.from_user.id}", WEEK, parametr)
        case "notInThisCity":
            cache.setex(f"result_where_did_buy_{callback_query.from_user.id}", WEEK, parametr)
        case "noneData":
            cache.setex(f"result_where_did_buy_{callback_query.from_user.id}", WEEK, parametr)
        case 'november':
            cache.setex(f"result_when_did_buy_{callback_query.from_user.id}", WEEK, parametr)
        case 'firstHalfDecember':
            cache.setex(f"result_when_did_buy_{callback_query.from_user.id}", WEEK, parametr)
        case '3weekDecember':
            cache.setex(f"result_when_did_buy_{callback_query.from_user.id}", WEEK, parametr)
        case '4weekDecember':
            cache.setex(f"result_when_did_buy_{callback_query.from_user.id}", WEEK, parametr)

    await s.witch_tree_more_eco(bot, callback_query)


@dp.callback_query_handler(lambda c: str(c.data).startswith('survey_step6'))
async def survey_step7(callback_query: types.CallbackQuery):
    
    parametr = callback_query.data.split('_')[-1]
    match parametr:
        case 'real':
            cache.setex(f"result_opinion_eco_tree_{callback_query.from_user.id}", WEEK, parametr)
        case 'plastic':
            cache.setex(f"result_opinion_eco_tree_{callback_query.from_user.id}", WEEK, parametr)
        case 'notAny':
            cache.setex(f"result_opinion_eco_tree_{callback_query.from_user.id}", WEEK, parametr)
    await bot.edit_message_text(
                    text=msg.survey_step7,
                    chat_id=callback_query.from_user.id,
                    message_id=cache.get(f'survey_msg_to_{callback_query.from_user.id}'),
                    reply_markup=types.InlineKeyboardMarkup()
                )
    await Form.eco.set()

@dp.message_handler(content_types=['text'], state=Form.eco)
async def survey_step8(message: types.Message, state: FSMContext):
    
    cache.setex(f"result_open_opinion_eco_tree_{message.from_user.id}", WEEK, message.text)
    await state.finish()
    await bot.delete_message(
        chat_id=message.from_user.id,
        message_id=cache.get(f"survey_msg_to_{message.from_user.id}")
    )
    msg_survey = await bot.send_message(
        chat_id=message.from_user.id,
        text=msg.survey_step8,
        reply_markup=InlineKeyboardMarkup().row(InlineKeyboardButton('Понравился 👍', callback_data='survey_step8_like'))\
            .row(InlineKeyboardButton('Не понравился 👎', callback_data='survey_step8_dontLike'))
    )
    cache.setex(f"survey_msg_to__{message.from_user.id}", WEEK, msg_survey.message_id)

@dp.callback_query_handler(lambda c: str(c.data).startswith('survey_step8'))
async def survey_step9(callback_query: types.CallbackQuery):
    
    await Form.feedback.set()
    parametr = callback_query.data.split('_')[-1]
    match parametr:
        case 'like':
            cache.setex(f"result_survey_{callback_query.from_user.id}", WEEK, parametr)
            await bot.edit_message_text(
                    text=msg.survey_step9_like,
                    chat_id=callback_query.from_user.id,
                    message_id=cache.get(f'survey_msg_to__{callback_query.from_user.id}'),
                    reply_markup=types.InlineKeyboardMarkup()
                )
        case 'dontLike':
            cache.setex(f"result_survey_{callback_query.from_user.id}", WEEK, parametr)
            await bot.edit_message_text(
                    text=msg.survey_step9_dontLike, 
                    chat_id=callback_query.from_user.id,
                    message_id=cache.get(f'survey_msg_to__{callback_query.from_user.id}'),
                    reply_markup=types.InlineKeyboardMarkup()
                )

@dp.message_handler(content_types=['text'], state=Form.feedback)
async def survey_step10(message: types.Message, state: FSMContext):
    await bot.send_message(message.from_user.id, 'Спасибо!\n\nСейчас (5-10 секунд) мы вам отправим результат вашего опроса в картинках.\n\nИ инструкцию, как нам можно помочь, а вам сделать подарок!\n\n')
    await types.ChatActions.upload_photo()
    await state.finish()
    cache.setex(f"result_survey_opinion_{message.from_user.id}", WEEK, message.text)
    media = types.MediaGroup()

    # собранные данные
    city = cache.get(f"result_city_{message.from_user.id}")
    tree = cache.get(f"result_tree_{message.from_user.id}")
    reason_tree = cache.get(f"result_reason_{message.from_user.id}")
    where_did_buy = cache.get(f"result_where_did_buy_{message.from_user.id}")
    when_did_buy = cache.get(f"result_when_did_buy_{message.from_user.id}")
    opinion_eco = cache.get(f"result_opinion_eco_tree_{message.from_user.id}")
    open_opinion_eco = cache.get(f"result_open_opinion_eco_tree_{message.from_user.id}")
    result_survey = cache.get(f"result_survey_{message.from_user.id}")
    result_survey_opinion = cache.get(f"result_survey_opinion_{message.from_user.id}")
    
    match tree:
        case 'realtree':
            link = 'stories_img/realtree/my_choise_real.jpg'
            media.attach_photo(types.InputFile(link))
        case 'plastictree':
            link ='stories_img/plastictree/my_choise_plastic.jpg'
            media.attach_photo(types.InputFile(link))
        case 'nonetree':
            if reason_tree == 'nonnewyear':
                link = 'stories_img/nonetree/my_choise_nonenewyear.jpg'
                media.attach_photo(types.InputFile(link))
            elif reason_tree == 'chineseyear':
                link = 'stories_img/nonetree/my_choise_chineseyear.jpg'
                media.attach_photo(types.InputFile(link))
            elif reason_tree == 'nowish':
                link = 'stories_img/nonetree/my_choise_nowish.jpg'
                media.attach_photo(types.InputFile(link))

    match reason_tree:
        case 'price':
            if tree == 'realtree':
                link = 'stories_img/realtree/reason/price.jpg'
                media.attach_photo(types.InputFile(link))
            elif tree == 'plastictree':
                link = 'stories_img/plastictree/reason/price.jpg'
                media.attach_photo(types.InputFile(link))
        case 'confort':
            if tree == 'realtree':
                link = 'stories_img/realtree/reason/comfort.jpg'
                media.attach_photo(types.InputFile(link))
            elif tree == 'plastictree':
                link = 'stories_img/plastictree/reason/comfort.jpg'
                media.attach_photo(types.InputFile(link))
        case 'like':
            if tree == 'realtree':
                link = 'stories_img/realtree/reason/like.jpg'
                media.attach_photo(types.InputFile(link))
            elif tree == 'plastictree':
                link = 'stories_img/plastictree/reason/like.jpg'
                media.attach_photo(types.InputFile(link))
        case 'long':            
            if tree == 'plastictree':
                link = 'stories_img/plastictree/reason/long.jpg'
                media.attach_photo(types.InputFile(link))
        case 'smell':            
            if tree == 'realtree':
                link = 'stories_img/realtree/reason/smell.jpg'
                media.attach_photo(types.InputFile(link))
    match when_did_buy:
        case 'thisYear':
            link = 'stories_img/plastictree/when/less1.jpg'
            media.attach_photo(types.InputFile(link))
        case '1or3YearAgo':
            link = 'stories_img/plastictree/when/more1.jpg'
            media.attach_photo(types.InputFile(link))
        case '4or7YearAgo':
            link = 'stories_img/plastictree/when/more3.jpg'
            media.attach_photo(types.InputFile(link))
        case 'more7YearAgo':
            link = 'stories_img/plastictree/when/more7.jpg'
            media.attach_photo(types.InputFile(link))
        case 'november':
            link = 'stories_img/realtree/when/nov.jpg'
            media.attach_photo(types.InputFile(link))
        case 'firstHalfDecember':
            link = 'stories_img/realtree/when/firsthalfdec.jpg'
            media.attach_photo(types.InputFile(link))
        case '3weekDecember':
            link = 'stories_img/realtree/when/3weekdec.jpg'
            media.attach_photo(types.InputFile(link))
        case '4weekDecember':
            link = 'stories_img/realtree/when/4weekdec.jpg'
            media.attach_photo(types.InputFile(link))
    link_share = 'stories_img/share.jpg'
    media.attach_photo(types.InputFile(link_share))
    await asyncio.sleep(2)
    await bot.send_media_group(
        chat_id=message.from_user.id,
        media=media,
    )
    user_deep_link = await get_start_link(message.from_user.id, encode=True)


    await db.insert_survey_result(
        tg_user_id=message.from_user.id,
        city=city,
        witch_tree=tree,
        why_this_choise=reason_tree,
        where_bought=where_did_buy,
        when_bought=when_did_buy,
        which_eco=opinion_eco,
        why_eco=open_opinion_eco,
        result_survey=result_survey,
        result_survey_opinion=result_survey_opinion
    )


    await bot.send_message(
        chat_id=message.from_user.id, 
        text=md.text(
            md.bold('Инструкция'),
            md.text(),
            md.text('Расскажите про наш опрос в соцсетях и выложите персональную ссылку\. Так друзья смогут написать вам открытку, анонимно или напрямую'),
            md.text(),
            md.text('1\. Сохраните картинки в ваш телефон; Скопируйте ссылку\.'),
            md.text(),
            md.text(md.code(user_deep_link)),
            md.text(),
            md.text('2\. Откройте Instagram\*; Пройдите в сторис; Выберите картинки из фотоплёнки\.'),
            md.text(''),
            md.text('3\. Нажмите на стикер; Выберите в списке «ссылку»; Вставьте в поле URL\.'),
            md.text(''),
            md.text('4\. Выкладывайте\! Вы великолепны\! Оставайтесь таким же в 2023\.'),
            md.text(),
            md.italic('*принадлежит Meta, признанной экстремистской в России'),
            sep='\n'
        ),
        parse_mode=types.ParseMode.MARKDOWN_V2)


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
