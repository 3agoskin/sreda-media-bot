"""Лучший формат оффера ever"""
# еще сделать сообщение для Ильи Красильщика
from aiogram import types
from aiogram.dispatcher.middlewares import BaseMiddleware


class OfferMiddleware(BaseMiddleware):
    def __init__(self, offer_username: str):
        self.offer_username = offer_username
        self.sent_offet = False
        super().__init__()
    
    async def on_process_message(self, message: types.Message, _):
        if str(message.from_user.username) == str(self.offer_username) and self.sent_offet == False:
            self.sent_offet = True 
            await message.answer("Оля, Привет! \n\nтут место для оффера")