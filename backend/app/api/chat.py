from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import current_user, role
from app.models import ChatSession, ChatMessage
from app.schemas import ChatInput
from app.services.chat_service import send
from app.repositories import serialize

router = APIRouter()


@router.post("/chat/messages")
async def message(data: ChatInput, user=Depends(current_user), db=Depends(get_db)):
    role(user, "patient")
    return await send(db, user, data)


@router.get("/chat/history")
async def history(
    session_id: int | None = None, user=Depends(current_user), db=Depends(get_db)
):
    role(user, "patient")
    sessions = (
        await db.scalars(
            select(ChatSession)
            .where(ChatSession.patient_id == user.id)
            .order_by(ChatSession.created_at.desc())
        )
    ).all()
    messages = []
    if session_id:
        if session_id not in [s.id for s in sessions]:
            raise HTTPException(404, "Диалог не найден")
        messages = (
            await db.scalars(
                select(ChatMessage)
                .where(ChatMessage.session_id == session_id)
                .order_by(ChatMessage.id)
            )
        ).all()
    return {
        "sessions": [serialize(s) for s in sessions],
        "messages": [serialize(m) for m in messages],
    }
