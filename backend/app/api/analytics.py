from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import current_user, access, role
from app.models import Consent, Report, Observation
from app.services.analytics_service import analytics, make_report
from app.schemas import FeedbackInput
from app.repositories import serialize
router=APIRouter()

async def exercise_scope(db,user,pid):
    if user.role=='patient': return True
    c=await db.scalar(select(Consent).where(Consent.patient_id==pid))
    return bool(c and c.share_exercises)

@router.get('/analytics/{patient_id}')
async def data(patient_id:int,days:int=Query(14,ge=1,le=30),user=Depends(current_user),db=Depends(get_db)):
    await access(db,user,patient_id,'analytics')
    return await analytics(db,patient_id,days,await exercise_scope(db,user,patient_id))

@router.post('/analytics/{patient_id}/report')
async def report(patient_id:int,days:int=Query(14,ge=1,le=30),user=Depends(current_user),db=Depends(get_db)):
    role(user,'psychologist')
    await access(db,user,patient_id,'analytics')
    r=await make_report(db,patient_id,user.id,days,await exercise_scope(db,user,patient_id))
    await db.commit()
    return serialize(r)

@router.get('/analytics/{patient_id}/reports')
async def reports(patient_id:int,user=Depends(current_user),db=Depends(get_db)):
    role(user,'psychologist')
    await access(db,user,patient_id,'analytics')
    rows=(await db.scalars(select(Report).where(Report.patient_id==patient_id,Report.psychologist_id==user.id).order_by(Report.created_at.desc()))).all()
    shared=await exercise_scope(db,user,patient_id)
    result=[]
    for r in rows:
        item=serialize(r)
        if not shared:
            item['report_data']={**item['report_data'],'completed_count':None,'assignment_count':None,'exercises_shared':False}
        result.append(item)
    return result

@router.put('/observations/{observation_id}/feedback')
async def feedback(observation_id:int,data:FeedbackInput,user=Depends(current_user),db=Depends(get_db)):
    role(user,'psychologist')
    o=await db.get(Observation,observation_id)
    if not o: raise HTTPException(404,'Наблюдение не найдено')
    await access(db,user,o.patient_id,'analytics')
    o.feedback=data.feedback
    await db.commit()
    return serialize(o)
