import logging

from aiogram import Dispatcher

from .core import config, storage, bot
from .handlers import UserHandlers

logging.basicConfig(level=logging.INFO)

dp: Dispatcher = Dispatcher(storage=storage)

dp.include_router(UserHandlers.router)


async def run_bot():
    await bot.delete_webhook(drop_pending_updates=False)

    await dp.start_polling(bot)
