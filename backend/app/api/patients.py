from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select, func, delete
from app.core.database import get_db
from app.core.security import current_user, role, access
from app.models import (
    User,
    Consent,
    TherapyPlan,
    JournalEntry,
    Assignment,
    Report,
    Observation,
    ChatSession,
    ChatMessage,
    AuthSession,
    now,
)
from app.schemas import ConsentInput, PlanInput
from app.repositories import public_user, serialize

router = APIRouter()


@router.get("/patients")
async def patients(user=Depends(current_user), db=Depends(get_db)):
    role(user, "psychologist")
    rows = (
        await db.execute(
            select(User, Consent)
            .join(Consent, Consent.patient_id == User.id)
            .where(Consent.psychologist_id == user.id, Consent.consent_status.is_(True))
        )
    ).all()
    result = []
    for p, c in rows:
        entries = (
            await db.scalar(
                select(func.count())
                .select_from(JournalEntry)
                .where(JournalEntry.patient_id == p.id)
            )
            if c.share_analytics
            else None
        )
        latest = (
            await db.scalar(
                select(func.max(JournalEntry.created_at)).where(
                    JournalEntry.patient_id == p.id
                )
            )
            if c.share_analytics
            else None
        )
        complete = (
            await db.scalar(
                select(func.count())
                .select_from(Assignment)
                .where(Assignment.patient_id == p.id, Assignment.status == "completed")
            )
            if c.share_exercises
            else None
        )
        total = (
            await db.scalar(
                select(func.count())
                .select_from(Assignment)
                .where(Assignment.patient_id == p.id)
            )
            if c.share_exercises
            else None
        )
        weekly = (
            await db.scalar(
                select(func.count())
                .select_from(JournalEntry)
                .where(
                    JournalEntry.patient_id == p.id,
                    JournalEntry.created_at >= now() - timedelta(days=7),
                )
            )
            if c.share_analytics
            else None
        )
        report_count = (
            await db.scalar(
                select(func.count())
                .select_from(Report)
                .where(
                    Report.patient_id == p.id,
                    Report.psychologist_id == user.id,
                    Report.created_at >= now() - timedelta(days=7),
                )
            )
            if c.share_analytics
            else None
        )
        result.append(
            {
                **public_user(p),
                "weekly_entries": weekly,
                "report_count": report_count,
                "entries": entries,
                "latest": latest,
                "completed": complete,
                "total": total,
                "consent": serialize(c),
            }
        )
    return result


@router.get("/patients/{patient_id}")
async def patient(patient_id: int, user=Depends(current_user), db=Depends(get_db)):
    await access(db, user, patient_id)
    p = await db.get(User, patient_id)
    if not p:
        raise HTTPException(404, "Пациент не найден")
    plan = await db.scalar(
        select(TherapyPlan).where(TherapyPlan.patient_id == patient_id)
    )
    consent = await db.scalar(select(Consent).where(Consent.patient_id == patient_id))
    return {
        **public_user(p),
        "plan": serialize(plan) if plan else None,
        "consent": serialize(consent) if consent else None,
    }


@router.get("/consent")
async def get_consent(user=Depends(current_user), db=Depends(get_db)):
    role(user, "patient")
    c = await db.scalar(select(Consent).where(Consent.patient_id == user.id))
    return serialize(c) if c else None


@router.put("/consent")
async def consent(data: ConsentInput, user=Depends(current_user), db=Depends(get_db)):
    role(user, "patient")
    c = await db.scalar(select(Consent).where(Consent.patient_id == user.id))
    if not c:
        raise HTTPException(404, "Связь с психологом отсутствует")
    for k, v in data.model_dump().items():
        setattr(c, k, v)
    await db.commit()
    return serialize(c)


@router.put("/therapy-plan/{patient_id}")
async def plan(
    patient_id: int, data: PlanInput, user=Depends(current_user), db=Depends(get_db)
):
    role(user, "psychologist")
    await access(db, user, patient_id)
    p = await db.scalar(select(TherapyPlan).where(TherapyPlan.patient_id == patient_id))
    if not p:
        p = TherapyPlan(patient_id=patient_id, psychologist_id=user.id)
        db.add(p)
    for k, v in data.model_dump().items():
        setattr(p, k, v)
    await db.commit()
    return serialize(p)


@router.delete("/me/data")
async def delete_data(
    response: Response, user=Depends(current_user), db=Depends(get_db)
):
    role(user, "patient")
    # Explicit deletion also keeps the SQLite test path equivalent to PostgreSQL cascades.
    session_ids = select(ChatSession.id).where(ChatSession.patient_id == user.id)
    await db.execute(delete(ChatMessage).where(ChatMessage.session_id.in_(session_ids)))
    for model in [
        Report,
        Observation,
        JournalEntry,
        Assignment,
        TherapyPlan,
        Consent,
        ChatSession,
    ]:
        await db.execute(delete(model).where(model.patient_id == user.id))
    await db.execute(delete(AuthSession).where(AuthSession.user_id == user.id))
    await db.delete(user)
    await db.commit()
    response.delete_cookie("mindprint_session", path="/")
    return {"ok": True}
