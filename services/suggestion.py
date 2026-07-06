from database.mongo import Mongo
from database.repositories.sentences import SentencesRepository


class SuggestionService:
    def __init__(self, mongo: Mongo) -> None:
        self.repo = SentencesRepository(mongo.db)

    async def submit(self, text: str, author: int) -> None:
        await self.repo.add(text=text, author=author)