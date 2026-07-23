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
        await self._ensure_sparse_unique("users", "telegram_id")
        await self._ensure_sparse_unique("users", "vk_id")
        await self.db.suggested_sentences.create_index("status")
        await self.db.suggested_sentences.create_index("source")
        await self.db.voice_records.create_index("sentence_id")
        await self.db.voice_records.create_index("telegram_id")
        await self.db.voice_records.create_index("vk_id")
        await self.db.voice_records.create_index("source")
        await self.db.need_translation.create_index("status")
        await self.db.need_translation.create_index("reviews.reviewer_id")

    async def _ensure_sparse_unique(self, collection: str, field: str) -> None:
        col = self.db[collection]
        index_name = f"{field}_1"
        info = await col.index_information()
        existing = info.get(index_name)
        if existing is not None:
            if existing.get("unique") and existing.get("sparse"):
                return
            await col.drop_index(index_name)
        await col.create_index(field, unique=True, sparse=True)

    async def close(self) -> None:
        if self.client:
            self.client.close()
