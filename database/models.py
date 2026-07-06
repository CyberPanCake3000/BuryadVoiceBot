from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class SentenceStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class User(BaseModel):
    telegram_id: int
    username: str | None = None
    language: str = "ru"
    agreed: bool = False
    agreed_at: datetime | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Translation(BaseModel):
    telegram_id: int
    text: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SuggestedSentence(BaseModel):
    text: str
    author: int
    status: SentenceStatus = SentenceStatus.PENDING
    moderator: int | None = None
    approved_at: datetime | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class VoiceRecord(BaseModel):
    sentence_id: str
    telegram_id: int
    telegram_file_id: str
    telegram_unique_id: str
    duration: int | None = None
    status: SentenceStatus = SentenceStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)