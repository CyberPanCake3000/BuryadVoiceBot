from aiogram.filters import BaseFilter
from aiogram.types import Message

from database.mongo import Mongo
from database.repositories.users import UsersRepository


class Agreed(BaseFilter):
    async def __call__(self, message: Message, mongo: Mongo) -> bool:
        users = UsersRepository(mongo.db)
        return await users.is_agreed(message.from_user.id)