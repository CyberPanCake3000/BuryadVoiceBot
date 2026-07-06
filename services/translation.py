from database.mongo import Mongo
from database.repositories.translations import TranslationsRepository


class TranslationService:
    def __init__(self, mongo: Mongo) -> None:
        self.repo = TranslationsRepository(mongo.db)

    async def next_batch(self, limit: int = 5) -> list[dict]:
        return await self.repo.random(limit=limit)