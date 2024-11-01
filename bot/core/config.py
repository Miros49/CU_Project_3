import os

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


storage = MemoryStorage()


@dataclass
class TgBot:
    token: str


@dataclass
class Config:
    tg_bot: TgBot


def load_config(path: str | None) -> Config:
    return Config(
        tg_bot=TgBot(
            token=os.getenv('BOT_TOKEN')
        )
    )


config: Config = load_config('.env')

default = DefaultBotProperties(parse_mode='HTML')
bot: Bot = Bot(token=config.tg_bot.token, default=default)
