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
            {"$unionWith": {
                "coll": "suggested_sentences",
                "pipeline": [
                    {"$unwind": "$reviews"},
                    {"$group": {
                        "_id": "$reviews.reviewer_id",
                        "reviews": {"$sum": 1},
                    }},
                ],
            }},
            {"$unionWith": {
                "coll": "need_translation",
                "pipeline": [
                    {"$unwind": "$reviews"},
                    {"$match": {"reviews.decision": {"$in": ["approve", "edit"]}}},
                    {"$group": {
                        "_id": "$reviews.reviewer_id",
                        "translation_reviews": {"$sum": 1},
                    }},
                ],
            }},
            {"$group": {
                "_id": "$_id",
                "suggestions": {"$sum": "$suggestions"},
                "rejected": {"$sum": "$rejected"},
                "voices": {"$sum": "$voices"},
                "reviews": {"$sum": "$reviews"},
                "translation_reviews": {"$sum": "$translation_reviews"},
            }},
            {"$addFields": {
                "rating": {
                    "$add": [
                        {"$subtract": [
                            {"$add": ["$suggestions", "$voices"]},
                            "$rejected",
                        ]},
                        "$reviews",
                        "$translation_reviews",
                    ]
                },
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
                {"status": "approved"}
            ),
            "total_voices": await voices.count_documents({}),
        }

    async def reviewer_stats(self) -> list[dict]:
        pipeline = [
            {"$unwind": "$reviews"},
            {"$group": {
                "_id": "$reviews.reviewer_id",
                "total": {"$sum": 1},
                "approved": {"$sum": {
                    "$cond": [{"$eq": ["$reviews.decision", "approve"]}, 1, 0]
                }},
                "rejected": {"$sum": {
                    "$cond": [{"$eq": ["$reviews.decision", "reject"]}, 1, 0]
                }},
                "edited": {"$sum": {
                    "$cond": [{"$eq": ["$reviews.decision", "edit"]}, 1, 0]
                }},
                "complained": {"$sum": {
                    "$cond": [{"$eq": ["$reviews.decision", "complain"]}, 1, 0]
                }},
            }},
            {"$sort": {"total": -1}},
            {"$lookup": {
                "from": "reviewers",
                "localField": "_id",
                "foreignField": "telegram_id",
                "as": "reviewer",
            }},
            {"$lookup": {
                "from": "users",
                "localField": "_id",
                "foreignField": "telegram_id",
                "as": "user",
            }},
            {"$addFields": {
                "username": {
                    "$ifNull": [
                        {"$first": "$user.username"},
                        {"$first": "$reviewer.full_name"},
                    ]
                },
            }},
            {"$project": {"reviewer": 0, "user": 0}},
        ]
        return [doc async for doc in self.db.suggested_sentences.aggregate(pipeline)]

    async def translation_reviewer_stats(self) -> list[dict]:
        pipeline = [
            {"$unwind": "$reviews"},
            {"$group": {
                "_id": "$reviews.reviewer_id",
                "total": {"$sum": 1},
                "approved": {"$sum": {
                    "$cond": [{"$eq": ["$reviews.decision", "approve"]}, 1, 0]
                }},
                "edited": {"$sum": {
                    "$cond": [{"$eq": ["$reviews.decision", "edit"]}, 1, 0]
                }},
                "skipped": {"$sum": {
                    "$cond": [{"$eq": ["$reviews.decision", "skip"]}, 1, 0]
                }},
            }},
            {"$sort": {"total": -1}},
            {"$lookup": {
                "from": "reviewers",
                "localField": "_id",
                "foreignField": "telegram_id",
                "as": "reviewer",
            }},
            {"$lookup": {
                "from": "users",
                "localField": "_id",
                "foreignField": "telegram_id",
                "as": "user",
            }},
            {"$addFields": {
                "username": {
                    "$ifNull": [
                        {"$first": "$user.username"},
                        {"$first": "$reviewer.full_name"},
                    ]
                },
            }},
            {"$project": {"reviewer": 0, "user": 0}},
        ]
        return [doc async for doc in self.db.need_translation.aggregate(pipeline)]