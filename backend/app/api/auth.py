from collections import defaultdict
import time
from argon2.exceptions import VerificationError
from fastapi import APIRouter, Depends, HTTPException, Response, Request
from sqlalchemy import select, delete
from app.core.database import get_db
from app.core.config import settings
from app.core.security import current_user, issue_session, hasher, digest
from app.models import User, AuthSession
from app.schemas import Login, DemoLogin
from app.repositories import public_user
router = APIRouter()
attempts = defaultdict(list)

def throttle(request):
    key = request.client.host if request.client else 'unknown'
    now = time.monotonic()
    attempts[key] = [t for t in attempts[key] if now-t < 60]
    if len(attempts[key]) >= 15:
        raise HTTPException(429, 'Слишком много попыток. Подождите минуту.')
    attempts[key].append(now)

@router.post('/auth/login')
async def login(data: Login, request: Request, response: Response, db=Depends(get_db)):
    throttle(request)
    user = await db.scalar(select(User).where(User.email == data.email.strip().lower()))
    valid = False
    if user:
        try:
            valid = hasher.verify(user.password_hash, data.password)
        except VerificationError:
            pass
    if not valid:
        raise HTTPException(401, 'Неверный email или пароль')
    await issue_session(db, user, response)
    return public_user(user)

@router.post('/auth/demo')
async def demo(data: DemoLogin, request: Request, response: Response, db=Depends(get_db)):
    throttle(request)
    if not settings().demo_mode:
        raise HTTPException(404, 'Демонстрационный вход выключен')
    user = await db.scalar(select(User).where(User.email == f'{data.role}@mindprint.demo', User.synthetic.is_(True)))
    if not user:
        raise HTTPException(404, 'Демоаккаунт отсутствует')
    await issue_session(db, user, response)
    return public_user(user)

@router.post('/auth/logout')
async def logout(request: Request, response: Response, db=Depends(get_db)):
    await db.execute(delete(AuthSession).where(AuthSession.token_hash == digest(request.cookies.get('mindprint_session',''))))
    await db.commit()
    response.delete_cookie('mindprint_session', path='/')
    return {'ok':True}

@router.get('/me')
async def me(user=Depends(current_user)):
    return public_user(user)

@router.get('/config')
async def config():
    return {'demo_mode':settings().demo_mode,'ai_provider':settings().ai_provider}
