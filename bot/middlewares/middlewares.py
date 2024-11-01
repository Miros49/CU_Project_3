import asyncio

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from typing import Callable, Dict, Any, Awaitable


class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, delay: float = 0.3):
        self.delay = delay
        super().__init__()

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:
        await asyncio.sleep(self.delay)
        return await handler(event, data)
