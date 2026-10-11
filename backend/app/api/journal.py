from datetime import timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import current_user, role, access
from app.models import JournalEntry, Assignment, now
from app.schemas import JournalInput
from app.repositories import serialize
from app.services.analytics_service import analyze
from app.services.ai.base import ProviderError

router = APIRouter()


@router.post("/journal")
async def create(data: JournalInput, user=Depends(current_user), db=Depends(get_db)):
    role(user, "patient")
    values = data.model_dump(exclude={"created_at"})
    when = data.created_at or now()
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    if when > now() + timedelta(minutes=5):
        raise HTTPException(422, "Дата не может быть в будущем")
    for aid in data.completed_exercises:
        a = await db.get(Assignment, aid)
        if not a or a.patient_id != user.id or a.status != "completed":
            raise HTTPException(
                422, "Можно отметить только своё выполненное упражнение"
            )
    entry = JournalEntry(patient_id=user.id, created_at=when, **values)
    db.add(entry)
    await db.flush()
    warning = None
    try:
        await analyze(db, [entry])
    except ProviderError as exc:
        entry.analysis_status = "unavailable"
        warning = str(exc)
    await db.commit()
    return {**serialize(entry), "warning": warning}


@router.get("/journal")
async def journal(
    patient_id: int | None = None, user=Depends(current_user), db=Depends(get_db)
):
    pid = patient_id or user.id
    await access(db, user, pid, "journal")
    rows = (
        await db.scalars(
            select(JournalEntry)
            .where(JournalEntry.patient_id == pid)
            .order_by(JournalEntry.created_at.desc())
            .limit(200)
        )
    ).all()
    return [serialize(e) for e in rows]
