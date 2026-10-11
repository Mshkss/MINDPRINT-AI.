import pytest
from sqlalchemy import select, func
from app.core.database import Session
from app.core.config import settings
from app.core.security import hasher
from app.models import User, Report, Waitlist, Observation, ChatSession, JournalEntry
from app.services.fixtures import DEMO_MESSAGE
from app.services.ai.base import validated_analysis
from app.services.ai.mock import MockProvider
from app.services.safety_service import safety_response

pytestmark = pytest.mark.asyncio


async def login(c, role):
    r = await c.post("/api/auth/demo", json={"role": role})
    assert r.status_code == 200, r.text
    return r.json()


async def test_auth_and_roles(client):
    assert (await client.get("/api/me")).status_code == 401
    assert (
        await client.post(
            "/api/auth/login",
            json={"email": "patient@mindprint.demo", "password": "bad"},
        )
    ).status_code == 401
    r = await client.post(
        "/api/auth/login",
        json={"email": "patient@mindprint.demo", "password": "test-only-password"},
    )
    assert r.status_code == 200
    assert "HttpOnly" in r.headers["set-cookie"]
    assert "password_hash" not in r.json()
    assert (await client.get("/api/patients")).status_code == 403
    assert (
        await client.put(
            "/api/therapy-plan/2",
            json={"focus_areas": [], "goals": [], "allowed_exercises": []},
        )
    ).status_code == 403
    await client.post("/api/auth/logout")
    assert (await client.get("/api/me")).status_code == 401
    settings().demo_mode = False
    assert (
        await client.post("/api/auth/demo", json={"role": "patient"})
    ).status_code == 404


async def test_full_assignment_chat_completion_report(client):
    await login(client, "psychologist")
    patients = (await client.get("/api/patients")).json()
    pid = patients[0]["id"]
    lib = (await client.get("/api/exercises/library")).json()
    thought = next(e for e in lib if e["type"] == "thought_diary")
    assigned = await client.post(
        "/api/exercises/assign", json={"patient_id": pid, "exercise_id": thought["id"]}
    )
    assert assigned.status_code == 200
    aid = assigned.json()["id"]
    await login(client, "patient")
    reply = await client.post("/api/chat/messages", json={"content": DEMO_MESSAGE})
    assert reply.status_code == 200, reply.text
    assert "Дневник мыслей" in reply.json()["message"]["content"]
    sid = reply.json()["session_id"]
    history = (await client.get(f"/api/chat/history?session_id={sid}")).json()
    assert len(history["messages"]) == 2
    assert history["messages"][0]["content"] == DEMO_MESSAGE
    assert (await client.post(f"/api/exercises/{aid}/complete")).status_code == 422
    for step in range(5):
        response = await client.post(
            f"/api/exercises/{aid}/answer",
            json={"answer": f"Мой ответ {step}", "expected_step": step},
        )
        assert response.status_code == 200
    done = await client.post(f"/api/exercises/{aid}/complete")
    assert done.json()["status"] == "completed"
    assert (
        await client.post(
            f"/api/exercises/{aid}/answer",
            json={"answer": "Повтор", "expected_step": 0},
        )
    ).status_code == 409
    await login(client, "psychologist")
    rows = (await client.get(f"/api/exercises?patient_id={pid}")).json()
    result = next(a for a in rows if a["id"] == aid)
    assert result["answers"] == [f"Мой ответ {step}" for step in range(5)]
    assert result["completed_at"]
    report = await client.post(f"/api/analytics/{pid}/report?days=14")
    assert report.status_code == 200, report.text
    report_data = report.json()["report_data"]
    assert report_data["completed_count"] == 2
    assert report_data["entry_count"] == 14
    assert report_data["observations"]
    observation = report_data["observations"][0]
    assert observation["evidence"]
    assert (
        await client.put(
            f'/api/observations/{observation["id"]}/feedback',
            json={"feedback": "confirmed"},
        )
    ).status_code == 200
    async with Session() as db:
        assert (await db.get(Observation, observation["id"])).feedback == "confirmed"
        assert await db.scalar(select(func.count()).select_from(Report)) == 1


async def test_journal_validation_and_evidence(patient):
    me = (await patient.get("/api/me")).json()
    r = await patient.post(
        "/api/journal",
        json={"mood_score": 2, "content": "Последние дни плохо сплю.", "tags": ["Сон"]},
    )
    assert r.status_code == 200
    entry = r.json()
    data = (await patient.get(f'/api/analytics/{me["id"]}')).json()
    observation = next(
        o for o in data["observations"] if o["journal_entry_id"] == entry["id"]
    )
    assert observation["evidence"] == "Последние дни плохо сплю."
    assert data["entry_count"] == 15
    assert (
        await patient.post("/api/journal", json={"mood_score": 6, "content": "x"})
    ).status_code == 422
    assert (
        await patient.post(
            "/api/journal", json={"mood_score": 3, "content": "x", "synthetic": True}
        )
    ).status_code == 422
    assert (
        await patient.post(
            "/api/journal",
            json={"mood_score": 3, "content": "x", "completed_exercises": [9999]},
        )
    ).status_code == 422


async def test_consent_revocation_blocks_every_surface(client):
    await login(client, "patient")
    pid = (await client.get("/api/me")).json()["id"]
    await client.put(
        "/api/consent",
        json={
            "consent_status": False,
            "share_journal": True,
            "share_analytics": True,
            "share_exercises": True,
        },
    )
    await login(client, "psychologist")
    assert pid not in [p["id"] for p in (await client.get("/api/patients")).json()]
    for path in [
        f"/api/patients/{pid}",
        f"/api/journal?patient_id={pid}",
        f"/api/exercises?patient_id={pid}",
        f"/api/analytics/{pid}",
        f"/api/analytics/{pid}/reports",
    ]:
        assert (await client.get(path)).status_code == 403, path
    assert (await client.post(f"/api/analytics/{pid}/report")).status_code == 403
    assert (
        await client.put(
            f"/api/therapy-plan/{pid}",
            json={"focus_areas": [], "goals": [], "allowed_exercises": []},
        )
    ).status_code == 403


async def test_granular_consent_hides_old_report_metrics(client):
    u = await login(client, "patient")
    pid = u["id"]
    await login(client, "psychologist")
    assert (await client.post(f"/api/analytics/{pid}/report")).status_code == 200
    await login(client, "patient")
    await client.put(
        "/api/consent",
        json={
            "consent_status": True,
            "share_journal": False,
            "share_analytics": True,
            "share_exercises": False,
        },
    )
    await login(client, "psychologist")
    assert (await client.get(f"/api/journal?patient_id={pid}")).status_code == 403
    assert (await client.get(f"/api/exercises?patient_id={pid}")).status_code == 403
    report = (await client.get(f"/api/analytics/{pid}/reports")).json()[0]
    assert report["report_data"]["completed_count"] is None
    analytics = (await client.get(f"/api/analytics/{pid}")).json()
    assert not analytics["exercises_shared"]


async def test_other_patient_and_psychologist_isolation(patient):
    assert (await patient.get("/api/patients/3")).status_code == 403
    assert (await patient.get("/api/journal?patient_id=3")).status_code == 403
    assert (await patient.get("/api/chat/history?session_id=999")).status_code == 404
    assert (
        await patient.post(
            "/api/exercises/4/answer", json={"answer": "x", "expected_step": 0}
        )
    ).status_code == 404
    async with Session() as db:
        db.add(
            User(
                name="Другой психолог",
                email="other@example.test",
                password_hash=hasher.hash("password"),
                role="psychologist",
            )
        )
        await db.commit()
    assert (
        await patient.post(
            "/api/auth/login",
            json={"email": "other@example.test", "password": "password"},
        )
    ).status_code == 200
    assert (await patient.get("/api/patients")).json() == []
    assert (await patient.get("/api/patients/2")).status_code == 403


async def test_external_provider_rejects_free_text_and_preserves_journal(patient):
    settings().ai_provider = "gigachat"
    r = await patient.post(
        "/api/chat/messages", json={"content": "Мои реальные персональные данные"}
    )
    assert r.status_code == 422
    r = await patient.post(
        "/api/journal", json={"mood_score": 3, "content": "Личная запись"}
    )
    assert r.status_code == 200
    assert r.json()["analysis_status"] == "unavailable"
    assert r.json()["warning"]
    assert (await patient.get("/api/journal")).json()[0]["content"] == "Личная запись"
    # Provider failure does not leave a partial chat behind.
    r = await patient.post("/api/chat/messages", json={"content": DEMO_MESSAGE})
    assert r.status_code == 503
    assert (await patient.get("/api/chat/history")).json()["sessions"] == []


async def test_external_rejects_previous_local_context(patient):
    r = await patient.post("/api/chat/messages", json={"content": DEMO_MESSAGE})
    sid = r.json()["session_id"]
    settings().ai_provider = "gigachat"
    response = await patient.post(
        "/api/chat/messages", json={"content": DEMO_MESSAGE, "session_id": sid}
    )
    assert response.status_code == 422


async def test_safety_bypasses_unavailable_provider(patient):
    settings().ai_provider = "gigachat"
    response = await patient.post(
        "/api/chat/messages", json={"content": "Я хочу убить себя"}
    )
    assert response.status_code == 200
    assert response.json()["safety"] == "crisis"
    assert "112" in response.json()["message"]["content"]
    assert not response.json()["assignments"]
    assert safety_response("Измени дозировку таблеток")["kind"] == "medical"


async def test_waitlist_unique_and_admin(client):
    payload = {"name": "Тест", "email": "USER@example.test", "role": "patient"}
    assert (await client.post("/api/waitlist", json=payload)).status_code == 200
    payload["email"] = "user@example.test"
    assert (await client.post("/api/waitlist", json=payload)).status_code == 200
    assert (await client.get("/api/waitlist/stats")).status_code == 401
    await login(client, "psychologist")
    assert (await client.get("/api/waitlist/stats")).status_code == 403
    async with Session() as db:
        assert await db.scalar(select(func.count()).select_from(Waitlist)) == 1
        db.add(
            User(
                name="Админ",
                email="admin@example.test",
                password_hash=hasher.hash("password"),
                role="admin",
            )
        )
        await db.commit()
    await client.post(
        "/api/auth/login", json={"email": "admin@example.test", "password": "password"}
    )
    assert (await client.get("/api/waitlist/stats")).json()["total"] == 1


async def test_delete_erases_account_and_dependents(patient):
    uid = (await patient.get("/api/me")).json()["id"]
    await patient.post("/api/chat/messages", json={"content": "Привет"})
    response = await patient.delete("/api/me/data")
    assert response.status_code == 200
    assert (await patient.get("/api/me")).status_code == 401
    async with Session() as db:
        assert await db.get(User, uid) is None
        assert (
            await db.scalar(
                select(func.count())
                .select_from(JournalEntry)
                .where(JournalEntry.patient_id == uid)
            )
            == 0
        )
        assert (
            await db.scalar(
                select(func.count())
                .select_from(ChatSession)
                .where(ChatSession.patient_id == uid)
            )
            == 0
        )


async def test_csrf(client):
    assert (
        await client.post(
            "/api/auth/demo",
            json={"role": "patient"},
            headers={"Origin": "https://evil.test"},
        )
    ).status_code == 403


async def test_mock_analysis_and_evidence_filter():
    raw = await MockProvider().analyze_entries(
        [{"id": 1, "content": "На работе тревожно"}]
    )
    assert len(raw["observations"]) == 2
    raw["observations"].append(
        {
            "entry_id": 1,
            "topic": "Сон",
            "evidence": "выдуманная цитата",
            "observation": "x",
        }
    )
    result = validated_analysis(raw, [{"id": 1, "content": "На работе тревожно"}])
    assert len(result["observations"]) == 2


async def test_plan_enforces_allowed_exercises(client):
    await login(client, "psychologist")
    pid = (await client.get("/api/patients")).json()[0]["id"]
    plan = {
        "focus_areas": ["рабочий стресс"],
        "goals": ["фиксировать триггеры тревоги"],
        "allowed_exercises": ["daily_reflection"],
        "reminders_enabled": True,
        "reminder_frequency": "weekly",
    }
    assert (await client.put(f"/api/therapy-plan/{pid}", json=plan)).status_code == 200
    assert (
        await client.post(
            "/api/exercises/assign", json={"patient_id": pid, "exercise_id": 1}
        )
    ).status_code == 422
    await login(client, "patient")
    rows = (await client.get("/api/exercises")).json()
    breathing = next(a for a in rows if a["exercise"]["type"] == "breathing")
    assert not breathing["available"]
    assert (
        await client.post(
            f'/api/exercises/{breathing["id"]}/answer',
            json={"answer": "x", "expected_step": 0},
        )
    ).status_code == 403
    reply = (
        await client.post("/api/chat/messages", json={"content": DEMO_MESSAGE})
    ).json()
    assert "Рефлексия дня" in reply["message"]["content"]
    assert "Дневник мыслей" not in reply["message"]["content"]


async def test_gigachat_policy_and_history_with_stub(patient, monkeypatch):
    from app.services import chat_service

    calls = []

    class Stub:
        async def chat(self, messages, context):
            calls.append((messages, context))
            return "Демонстрационный ответ"

    monkeypatch.setattr(chat_service, "provider", lambda: Stub())
    settings().ai_provider = "gigachat"
    r = await patient.post("/api/chat/messages", json={"content": DEMO_MESSAGE})
    assert r.status_code == 200
    sid = r.json()["session_id"]
    r = await patient.post(
        "/api/chat/messages", json={"content": "Хочу поговорить", "session_id": sid}
    )
    assert r.status_code == 200
    assert len(calls[1][0]) == 3
    assert "recent_journal" not in calls[1][1]
    assert "name" not in calls[1][1]
    assert calls[1][1]["therapy_plan"]["focus"]
    async with Session() as db:
        from app.models import TherapyPlan

        plan = await db.scalar(select(TherapyPlan).where(TherapyPlan.patient_id == 2))
        plan.goals = ["Произвольные приватные данные"]
        await db.commit()
    assert (
        await patient.post("/api/chat/messages", json={"content": DEMO_MESSAGE})
    ).status_code == 422
    assert len(calls) == 2
