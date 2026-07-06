from database.mongo import Mongo
from database.repositories.voices import VoicesRepository


class VoiceService:
    def __init__(self, mongo: Mongo) -> None:
        self.repo = VoicesRepository(mongo.db)

    async def save(
        self, sentence_id, telegram_id: int,
        file_id: str, unique_id: str, duration: int | None,
    ) -> None:
        await self.repo.add(sentence_id, telegram_id, file_id, unique_id, duration)