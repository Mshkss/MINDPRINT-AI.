from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict, field_validator


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Login(Input):
    email: str = Field(max_length=254)
    password: str = Field(max_length=256)


class DemoLogin(Input):
    role: Literal["patient", "psychologist"]


class JournalInput(Input):
    mood_score: int = Field(ge=1, le=5)
    content: str = Field(default="", max_length=10000)
    tags: list[str] = Field(default_factory=list, max_length=10)
    completed_exercises: list[int] = Field(default_factory=list, max_length=20)
    created_at: datetime | None = None


class ChatInput(Input):
    content: str = Field(min_length=1, max_length=4000)
    session_id: int | None = None


class PlanInput(Input):
    focus_areas: list[str] = Field(max_length=15)
    goals: list[str] = Field(max_length=15)
    allowed_exercises: list[Literal["thought_diary", "breathing", "daily_reflection"]]
    reminders_enabled: bool = False
    reminder_frequency: Literal["daily", "weekly"] = "daily"

    @field_validator("focus_areas", "goals")
    @classmethod
    def limit_text(cls, values):
        if any(len(v) > 300 for v in values):
            raise ValueError("Слишком длинный текст")
        return values


class ConsentInput(Input):
    consent_status: bool
    share_journal: bool
    share_analytics: bool
    share_exercises: bool


class AssignInput(Input):
    patient_id: int
    exercise_id: int


class AnswerInput(Input):
    answer: str = Field(min_length=1, max_length=4000)
    expected_step: int = Field(ge=0, le=10)


class FeedbackInput(Input):
    feedback: Literal["confirmed", "incorrect", "discuss"]


class WaitlistInput(Input):
    name: str = Field(min_length=1, max_length=120)
    email: str = Field(
        min_length=3, max_length=254, pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$"
    )
    role: Literal["patient", "psychologist"]

    @field_validator("email")
    @classmethod
    def normalize(cls, value):
        return value.strip().lower()


class Finding(BaseModel):
    entry_id: int
    topic: str = Field(max_length=100)
    evidence: str = Field(min_length=1, max_length=10000)
    observation: str = Field(max_length=500)


class Analysis(BaseModel):
    observations: list[Finding] = Field(default_factory=list, max_length=100)
