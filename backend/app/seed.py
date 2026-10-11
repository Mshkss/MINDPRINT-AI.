import asyncio
import secrets
from datetime import timedelta
from sqlalchemy import select
from app.core.database import Session
from app.core.config import settings
from app.core.security import hasher
from app.models import (
    User,
    Consent,
    TherapyPlan,
    JournalEntry,
    Exercise,
    Assignment,
    ChatSession,
    ChatMessage,
    now,
)
from app.services.fixtures import DEMO_TEXTS, DEMO_FOCUS, DEMO_GOALS
from app.services.ai.mock import MockProvider
from app.models import Observation


async def seed():
    if not settings().demo_mode or not settings().seed_demo:
        return
    async with Session() as db:
        if await db.scalar(select(User.id).limit(1)):
            return
        password = settings().demo_password or secrets.token_urlsafe(32)
        psych = User(
            name="Анна Смирнова",
            email="psychologist@mindprint.demo",
            password_hash=hasher.hash(password),
            role="psychologist",
            synthetic=True,
        )
        db.add(psych)
        await db.flush()
        exercises = [
            Exercise(
                name="Дневник мыслей",
                description="Отделить факты от предположений и посмотреть на ситуацию по-новому.",
                type="thought_diary",
                steps=[
                    "Что произошло?",
                    "Какая мысль возникла?",
                    "Какие эмоции ты испытал?",
                    "Какие есть факты за и против этой мысли?",
                    "Как можно иначе посмотреть на ситуацию?",
                ],
            ),
            Exercise(
                name="Дыхательная практика",
                description="Две минуты спокойного дыхания в комфортном темпе.",
                type="breathing",
                steps=["Дыхательная практика завершена"],
            ),
            Exercise(
                name="Рефлексия дня",
                description="Найти опоры и заметить то, что получилось сегодня.",
                type="daily_reflection",
                steps=[
                    "Что сегодня было самым сложным?",
                    "Что получилось хорошо?",
                    "Что помогло справиться?",
                    "Что хотелось бы обсудить с психологом?",
                ],
            ),
        ]
        db.add_all(exercises)
        await db.flush()
        for idx, name in enumerate(["Александр", "Мария", "Дмитрий"]):
            patient = User(
                name=name,
                email=(
                    "patient@mindprint.demo"
                    if idx == 0
                    else f"patient{idx}@mindprint.demo"
                ),
                password_hash=hasher.hash(password),
                role="patient",
                synthetic=True,
            )
            db.add(patient)
            await db.flush()
            db.add(Consent(psychologist_id=psych.id, patient_id=patient.id))
            db.add(
                TherapyPlan(
                    patient_id=patient.id,
                    psychologist_id=psych.id,
                    focus_areas=DEMO_FOCUS,
                    goals=DEMO_GOALS,
                    allowed_exercises=[
                        "thought_diary",
                        "breathing",
                        "daily_reflection",
                    ],
                )
            )
            mood = (
                [4, 4, 3, 4, 3, 2, 3, 2, 2, 1, 2, 3, 3, 4]
                if idx == 0
                else (
                    [3, 4, 4, 3, 4, 4, 5, 4, 3, 4, 4, 4, 5, 4]
                    if idx == 1
                    else [3, 3, 4, 3, 2, 3, 3, 2, 3, 3, 3, 4, 3, 3]
                )
            )
            for day, content in enumerate(DEMO_TEXTS):
                entry = JournalEntry(
                    patient_id=patient.id,
                    mood_score=mood[day],
                    content=content,
                    tags=[],
                    synthetic=True,
                    analysis_status="done",
                    created_at=now() - timedelta(days=13 - day, hours=2),
                )
                db.add(entry)
                await db.flush()
                result = await MockProvider().analyze_entries(
                    [{"id": entry.id, "content": content}]
                )
                for o in result["observations"]:
                    db.add(
                        Observation(
                            patient_id=patient.id,
                            journal_entry_id=entry.id,
                            observation_type=o["topic"],
                            observation_data={"text": o["observation"]},
                            evidence=o["evidence"],
                        )
                    )
            for n, ex in enumerate(exercises):
                db.add(
                    Assignment(
                        patient_id=patient.id,
                        psychologist_id=psych.id,
                        exercise_id=ex.id,
                        status="completed" if n == 0 else "assigned",
                        answers=(
                            ["Демонстрационный ответ"] * len(ex.steps) if n == 0 else []
                        ),
                        created_at=now() - timedelta(days=2),
                        completed_at=now() - timedelta(days=1) if n == 0 else None,
                    )
                )
        await db.commit()


if __name__ == "__main__":
    asyncio.run(seed())
