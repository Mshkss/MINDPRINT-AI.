import hashlib
import secrets
from datetime import timedelta
from argon2 import PasswordHasher
from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from app.core.database import get_db
from app.core.config import settings
from app.models import User, AuthSession, Consent, now

hasher = PasswordHasher()

def digest(token):
    return hashlib.sha256(token.encode()).hexdigest()

async def issue_session(db, user, response):
    token = secrets.token_urlsafe(40)
    db.add(AuthSession(token_hash=digest(token), user_id=user.id, expires_at=now()+timedelta(hours=12)))
    await db.commit()
    response.set_cookie('mindprint_session', token, httponly=True, secure=settings().cookie_secure, samesite='lax', max_age=43200, path='/')

async def current_user(request: Request, db=Depends(get_db)):
    token = request.cookies.get('mindprint_session', '')
    user = await db.scalar(select(User).join(AuthSession).where(AuthSession.token_hash == digest(token), AuthSession.expires_at > now()))
    if not user:
        raise HTTPException(401, 'Войдите в аккаунт')
    return user

def role(user, required):
    if user.role != required:
        raise HTTPException(403, 'Недостаточно прав')

async def access(db, user, patient_id, scope=None):
    if user.role == 'patient' and user.id == patient_id:
        return
    if user.role != 'psychologist':
        raise HTTPException(403, 'Доступ запрещён')
    consent = await db.scalar(select(Consent).where(Consent.patient_id == patient_id, Consent.psychologist_id == user.id, Consent.consent_status.is_(True)))
    if not consent or (scope and not getattr(consent, 'share_'+scope)):
        raise HTTPException(403, 'Нет действующего согласия на эти данные')
