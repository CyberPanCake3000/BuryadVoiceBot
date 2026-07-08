from motor.motor_asyncio import AsyncIOMotorDatabase

from database.models import SentenceStatus


class StatsRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.db = db
        self.col = db.suggested_sentences

    async def top(self, limit: int = 5) -> list[dict]:
        pipeline = [
            {"$group": {
                "_id": "$author",
                "suggestions": {"$sum": 1},
                "rejected": {"$sum": {
                    "$cond": [{"$eq": ["$status", SentenceStatus.REJECTED]}, 1, 0]
                }},
            }},
            {"$unionWith": {
                "coll": "voice_records",
                "pipeline": [
                    {"$group": {"_id": "$telegram_id", "voices": {"$sum": 1}}},
                ],
            }},
            {"$group": {
                "_id": "$_id",
                "suggestions": {"$sum": "$suggestions"},
                "rejected": {"$sum": "$rejected"},
                "voices": {"$sum": "$voices"},
            }},
            {"$addFields": {
                "rating": {"$subtract": [
                    {"$add": ["$suggestions", "$voices"]}, "$rejected"
                ]},
            }},
            {"$sort": {"rating": -1, "_id": 1}},
            {"$limit": limit},
            {"$lookup": {
                "from": "users",
                "localField": "_id",
                "foreignField": "telegram_id",
                "as": "user",
            }},
            {"$addFields": {"username": {"$first": "$user.username"}}},
            {"$project": {"user": 0}},
        ]
        return [doc async for doc in self.col.aggregate(pipeline)]

    async def overview(self) -> dict:
        suggested = self.db.suggested_sentences
        voices = self.db.voice_records
        translations = self.db.need_translation
        users = self.db.users
        return {
            "participants": await users.count_documents({"agreed": True}),
            "total_suggestions": await suggested.count_documents({}),
            "approved": await suggested.count_documents(
                {"status": SentenceStatus.APPROVED}
            ),
            "translated": await translations.count_documents(
                {"status": "translated"}
            ),
            "total_voices": await voices.count_documents({}),
        }