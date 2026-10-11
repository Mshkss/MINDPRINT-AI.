from fastapi import HTTPException
from sqlalchemy import select
from app.models import Assignment, Exercise, TherapyPlan, Consent
from app.repositories import serialize

async def assignments(db, patient_id):
    rows = (await db.execute(select(Assignment, Exercise).join(Exercise).where(Assignment.patient_id == patient_id).order_by(Assignment.created_at.desc()))).all()
    return [{**serialize(a), 'exercise':serialize(e)} for a,e in rows]

async def active_assignments(db, patient_id):
    plan = await db.scalar(select(TherapyPlan).where(TherapyPlan.patient_id == patient_id))
    consent = await db.scalar(select(Consent).where(Consent.patient_id == patient_id))
    if not plan or not consent or not consent.consent_status:
        return []
    return [a for a in await assignments(db, patient_id) if a['status'] != 'completed' and a['exercise']['type'] in plan.allowed_exercises]

async def require_assignment(db, user, assignment_id):
    assignment = await db.scalar(select(Assignment).where(Assignment.id == assignment_id, Assignment.patient_id == user.id).with_for_update())
    if not assignment:
        raise HTTPException(404, 'Упражнение не найдено')
    exercise = await db.get(Exercise, assignment.exercise_id)
    allowed = await active_assignments(db, user.id)
    if assignment.status != 'completed' and assignment.id not in [a['id'] for a in allowed]:
        raise HTTPException(403, 'Упражнение недоступно в текущем согласованном плане')
    return assignment, exercise
