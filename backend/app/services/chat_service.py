from sqlalchemy import select
from fastapi import HTTPException
from app.models import ChatSession, ChatMessage, TherapyPlan, JournalEntry
from app.core.config import settings
from app.services.ai import provider
from app.services.ai.base import ProviderError
from app.services.fixtures import DEMO_CHAT_INPUTS, DEMO_FOCUS, DEMO_GOALS
from app.services.safety_service import safety_response
from app.services.therapy_service import active_assignments


async def send(db, user, payload):
    session = (
        await db.get(ChatSession, payload.session_id) if payload.session_id else None
    )
    if payload.session_id and (not session or session.patient_id != user.id):
        raise HTTPException(404, "Диалог не найден")
    safe = safety_response(payload.content)
    previous = (
        list(
            (
                await db.scalars(
                    select(ChatMessage)
                    .where(ChatMessage.session_id == session.id)
                    .order_by(ChatMessage.id.desc())
                    .limit(30)
                )
            ).all()
        )[::-1]
        if session
        else []
    )
    plan = await db.scalar(select(TherapyPlan).where(TherapyPlan.patient_id == user.id))
    assigned = await active_assignments(db, user.id)
    external = settings().ai_provider == "gigachat"
    if external and not safe:
        if (
            not settings().demo_mode
            or not user.synthetic
            or payload.content not in DEMO_CHAT_INPUTS
        ):
            raise HTTPException(
                422,
                "GigaChat принимает только встроенные демосообщения. Для свободного ввода используйте mock или локальную модель.",
            )
        if any(
            not m.external_safe
            or (m.role == "user" and m.content not in DEMO_CHAT_INPUTS)
            for m in previous
        ):
            raise HTTPException(
                422,
                "Этот диалог содержит свободный текст. Начните новый демонстрационный диалог.",
            )
        if plan and (
            any(x not in DEMO_FOCUS for x in plan.focus_areas)
            or any(x not in DEMO_GOALS for x in plan.goals)
        ):
            raise HTTPException(
                422,
                "План изменён и не может передаваться во внешний AI. Используйте локальный провайдер.",
            )
    context = {
        "therapy_plan": (
            {
                "focus": plan.focus_areas,
                "goals": plan.goals,
                "allowed_exercises": plan.allowed_exercises,
            }
            if plan
            else {}
        ),
        "assignments": [
            {"id": a["id"], "name": a["exercise"]["name"]} for a in assigned
        ],
    }
    if not external:
        recent = (
            await db.scalars(
                select(JournalEntry)
                .where(JournalEntry.patient_id == user.id)
                .order_by(JournalEntry.created_at.desc())
                .limit(4)
            )
        ).all()
        context["recent_journal"] = [e.content for e in recent]
    messages = [{"role": m.role, "content": m.content} for m in previous] + [
        {"role": "user", "content": payload.content}
    ]
    answer = safe["content"] if safe else await provider().chat(messages, context)
    if not session:
        session = ChatSession(patient_id=user.id, title=payload.content[:70])
        db.add(session)
        await db.flush()
    db.add(
        ChatMessage(
            session_id=session.id,
            role="user",
            content=payload.content,
            external_safe=external and not bool(safe),
        )
    )
    reply = ChatMessage(
        session_id=session.id,
        role="assistant",
        content=answer,
        external_safe=external and not bool(safe),
    )
    db.add(reply)
    await db.commit()
    return {
        "session_id": session.id,
        "message": {
            "id": reply.id,
            "role": "assistant",
            "content": answer,
            "created_at": reply.created_at,
        },
        "safety": safe["kind"] if safe else None,
        "assignments": [] if safe else assigned,
    }
