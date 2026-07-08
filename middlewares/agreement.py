from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import Message

from database.mongo import Mongo
from database.repositories.users import UsersRepository

ALLOWED_WITHOUT_AGREEMENT = {"/start", "/help", "/policy", "/leaderboard", "/stat"}


class AgreementMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any],
    ) -> Any:
        mongo: Mongo = data["mongo"]
        users = UsersRepository(mongo.db)
        # забаненные — полный стоп, раньше всех проверок
        if await users.is_banned(event.from_user.id):
            return None

        if event.chat.type in ("group", "supergroup"):
            return await handler(event, data)

        text = (event.text or "").strip()
        if text in ALLOWED_WITHOUT_AGREEMENT:
            return await handler(event, data)

        mongo: Mongo = data["mongo"]
        users = UsersRepository(mongo.db)
        if await users.is_agreed(event.from_user.id):
            return await handler(event, data)

        await event.answer("Сначала примите политику обработки данных — /start")
        return None