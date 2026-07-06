from database.mongo import Mongo
from database.repositories.users import UsersRepository


class UserService:
    def __init__(self, mongo: Mongo) -> None:
        self.users = UsersRepository(mongo.db)

    async def register(self, telegram_id: int, username: str | None) -> None:
        await self.users.upsert(telegram_id, username)