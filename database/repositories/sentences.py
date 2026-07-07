from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorDatabase

from database.models import SentenceStatus


class SentencesRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.col = db.suggested_sentences

    async def add(self, text: str, author: int) -> None:
        result = await self.col.insert_one({
            "text": text,
            "author": author,
            "status": SentenceStatus.PENDING,
            "moderator": None,
            "reviews": [],
            "approved_at": None,
            "created_at": datetime.utcnow(),
        })
        return result.inserted_id

    async def random_approved(self, limit: int = 5) -> list[dict]:
        cursor = self.col.aggregate([
            {"$match": {"status": SentenceStatus.APPROVED}},
            {"$sample": {"size": limit}},
        ])
        return [doc async for doc in cursor]

    async def set_status(
        self, doc_id, status: SentenceStatus, moderator: int
    ) -> None:
        await self.col.update_one(
            {"_id": doc_id},
            {"$set": {
                "status": status,
                "moderator": moderator,
                "approved_at": datetime.utcnow(),
            }},
        )

    async def random_unreviewed(self, reviewer_id: int, limit: int = 5) -> list[dict]:
        cursor = self.col.aggregate([
            {"$match": {
                "status": SentenceStatus.PENDING,
                "reviews.reviewer_id": {"$ne": reviewer_id}, 
            }},
            {"$sample": {"size": limit}},
        ])
        return [doc async for doc in cursor]

    async def add_review(self, doc_id, reviewer_id: int, decision: str) -> bool:
        result = await self.col.update_one(
            {"_id": doc_id, "reviews.reviewer_id": {"$ne": reviewer_id}},
            {"$push": {"reviews": {
                "reviewer_id": reviewer_id,
                "decision": decision,
                "created_at": datetime.utcnow(),
            }}},
        )
        return result.modified_count == 1

    async def recalc_status(self, doc_id, total_reviewers: int) -> str | None:
        doc = await self.col.find_one({"_id": doc_id}, {"reviews": 1})
        if doc is None:
            return None
        reviews = doc.get("reviews", [])
        approvals = sum(1 for r in reviews if r["decision"] == "approve")
        rejections = sum(1 for r in reviews if r["decision"] == "reject")

        new_status = None
        if approvals * 2 > total_reviewers:
            new_status = SentenceStatus.APPROVED
        elif rejections * 2 > total_reviewers:
            new_status = SentenceStatus.REJECTED

        if new_status:
            await self.col.update_one(
                {"_id": doc_id},
                {"$set": {"status": new_status, "approved_at": datetime.utcnow()}},
            )
        return new_status