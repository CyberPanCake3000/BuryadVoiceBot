from aiogram.filters import BaseFilter
from aiogram.types import Message

from database.mongo import Mongo
from database.repositories.reviewers import ReviewersRepository


class IsReviewer(BaseFilter):
    async def __call__(self, message: Message, mongo: Mongo) -> bool:
        reviewers = ReviewersRepository(mongo.db)
        return await reviewers.is_reviewer(message.from_user.id)