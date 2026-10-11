from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import current_user, role, access
from app.models import Exercise, Assignment, TherapyPlan, now
from app.schemas import AssignInput, AnswerInput
from app.services.therapy_service import (
    assignments,
    active_assignments,
    require_assignment,
)
from app.repositories import serialize

router = APIRouter()


@router.get("/exercises/library")
async def library(user=Depends(current_user), db=Depends(get_db)):
    return [serialize(e) for e in (await db.scalars(select(Exercise))).all()]


@router.get("/exercises")
async def exercises(
    patient_id: int | None = None, user=Depends(current_user), db=Depends(get_db)
):
    pid = patient_id or user.id
    await access(db, user, pid, "exercises")
    available = {a["id"] for a in await active_assignments(db, pid)}
    return [
        {**a, "available": a["id"] in available} for a in await assignments(db, pid)
    ]


@router.post("/exercises/assign")
async def assign(data: AssignInput, user=Depends(current_user), db=Depends(get_db)):
    role(user, "psychologist")
    await access(db, user, data.patient_id, "exercises")
    plan = await db.scalar(
        select(TherapyPlan).where(TherapyPlan.patient_id == data.patient_id)
    )
    e = await db.get(Exercise, data.exercise_id)
    if not e or not plan or e.type not in plan.allowed_exercises:
        raise HTTPException(422, "Сначала разрешите упражнение в плане сопровождения")
    existing = await db.scalar(
        select(Assignment).where(
            Assignment.patient_id == data.patient_id,
            Assignment.exercise_id == e.id,
            Assignment.status != "completed",
        )
    )
    if existing:
        return serialize(existing)
    a = Assignment(
        patient_id=data.patient_id, psychologist_id=user.id, exercise_id=e.id
    )
    db.add(a)
    await db.commit()
    return serialize(a)


@router.post("/exercises/{assignment_id}/answer")
async def answer(
    assignment_id: int,
    data: AnswerInput,
    user=Depends(current_user),
    db=Depends(get_db),
):
    role(user, "patient")
    a, e = await require_assignment(db, user, assignment_id)
    if (
        a.status == "completed"
        or len(a.answers) != data.expected_step
        or len(a.answers) >= len(e.steps)
    ):
        raise HTTPException(409, "Шаг уже изменился. Обновите упражнение.")
    a.answers = [*a.answers, data.answer]
    a.status = "in_progress"
    await db.commit()
    return serialize(a)


@router.post("/exercises/{assignment_id}/complete")
async def complete(assignment_id: int, user=Depends(current_user), db=Depends(get_db)):
    role(user, "patient")
    a, e = await require_assignment(db, user, assignment_id)
    if len(a.answers) != len(e.steps):
        raise HTTPException(422, "Сначала пройдите все шаги упражнения")
    if a.status != "completed":
        a.status = "completed"
        a.completed_at = now()
        await db.commit()
    return serialize(a)
