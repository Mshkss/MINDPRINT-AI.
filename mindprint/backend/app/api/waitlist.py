from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from app.core.database import get_db
from app.core.security import current_user, role
from app.models import Waitlist
from app.schemas import WaitlistInput
router=APIRouter()

@router.post('/waitlist')
async def join(data:WaitlistInput,db=Depends(get_db)):
    db.add(Waitlist(**data.model_dump()))
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
    return {'ok':True,'message':'Спасибо! Заявка принята.'}

@router.get('/waitlist/stats')
async def stats(user=Depends(current_user),db=Depends(get_db)):
    role(user,'admin')
    rows=(await db.execute(select(Waitlist.role,func.count()).group_by(Waitlist.role))).all()
    return {'total':sum(v for _,v in rows),'by_role':dict(rows),'target':100}
