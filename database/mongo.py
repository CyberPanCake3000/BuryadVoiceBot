from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase


class Mongo:
    def __init__(self, uri: str, db_name: str) -> None:
        self._uri = uri
        self._db_name = db_name
        self.client: AsyncIOMotorClient | None = None
        self.db: AsyncIOMotorDatabase | None = None

    async def connect(self) -> None:
        self.client = AsyncIOMotorClient(self._uri)
        self.db = self.client[self._db_name]

    async def ensure_indexes(self) -> None:
        await self.db.users.create_index("telegram_id", unique=True)
        await self.db.suggested_sentences.create_index("status")
        await self.db.voice_records.create_index("sentence_id")
        await self.db.voice_records.create_index("telegram_id")
        await self.db.need_translation.create_index("status")
        await self.db.need_translation.create_index("reviews.reviewer_id")

    async def close(self) -> None:
        if self.client:
            self.client.close()