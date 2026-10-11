from collections import Counter
from fastapi.encoders import jsonable_encoder
from datetime import timedelta
from sqlalchemy import select
from app.models import JournalEntry, Observation, Report, now
from app.services.ai import provider
from app.services.ai.base import validated_analysis, ProviderError
from app.services.fixtures import DEMO_TEXTS
from app.core.config import settings
from app.repositories import serialize
from app.services.therapy_service import assignments

async def analyze(db, entries):
    if settings().ai_provider == 'gigachat' and (not settings().demo_mode or any(not e.synthetic or e.content not in DEMO_TEXTS for e in entries)):
        raise ProviderError('Внешний AI доступен только для встроенных синтетических записей. Запись сохранена без анализа.')
    payload = [{'id':e.id,'content':e.content} for e in entries if e.content]
    try:
        result = validated_analysis(await provider().analyze_entries(payload), payload)
    except ProviderError:
        raise
    except Exception as exc:
        raise ProviderError('Не удалось проверить структуру ответа AI. Запись сохранена.') from exc
    for o in result['observations']:
        existing = await db.scalar(select(Observation).where(Observation.journal_entry_id == o['entry_id'], Observation.observation_type == o['topic']))
        if not existing:
            entry = next(e for e in entries if e.id == o['entry_id'])
            db.add(Observation(patient_id=entry.patient_id, journal_entry_id=entry.id, observation_type=o['topic'], observation_data={'text':o['observation']}, evidence=o['evidence']))
    for e in entries:
        e.analysis_status = 'done'
    await db.flush()

async def analytics(db, patient_id, days=14, include_exercises=True):
    since = now() - timedelta(days=days)
    entries = list((await db.scalars(select(JournalEntry).where(JournalEntry.patient_id == patient_id, JournalEntry.created_at >= since).order_by(JournalEntry.created_at))).all())
    observations = list((await db.scalars(select(Observation).join(JournalEntry).where(Observation.patient_id == patient_id, JournalEntry.created_at >= since).order_by(JournalEntry.created_at.desc()))).all())
    grouped = {}
    for e in entries:
        day = e.created_at.date().isoformat()
        grouped.setdefault(day, []).append(e.mood_score)
    series = [{'date':d,'mood':round(sum(v)/len(v),2),'entries':len(v)} for d,v in grouped.items()]
    ex = await assignments(db, patient_id) if include_exercises else []
    completed = [a for a in ex if a['completed_at'] and a['completed_at'].replace(tzinfo=since.tzinfo) >= since]
    return {'days':days, 'series':series, 'entry_count':len(entries), 'average_mood':round(sum(e.mood_score for e in entries)/len(entries),1) if entries else None, 'topics':[{'name':k,'count':v} for k,v in Counter(o.observation_type for o in observations).most_common()], 'observations':[serialize(o) for o in observations], 'completed_count':len(completed), 'assignment_count':len(ex), 'exercises_shared':include_exercises}

async def make_report(db, patient_id, psychologist_id, days, include_exercises):
    since = now() - timedelta(days=days)
    entries = list((await db.scalars(select(JournalEntry).where(JournalEntry.patient_id == patient_id, JournalEntry.created_at >= since))).all())
    await analyze(db, entries)
    data = await analytics(db, patient_id, days, include_exercises)
    series = data['series']
    change = round(series[-1]['mood']-series[0]['mood'],1) if len(series)>1 else None
    data['summary'] = f'За {days} дней сохранено записей: {len(entries)}. ' + (f'Разница между последним и первым дневным значением настроения: {change:+g}.' if change is not None else 'Недостаточно данных для сравнения.')
    data['questions'] = [f'Как тема «{t["name"].lower()}» влияла на ваше самочувствие?' for t in data['topics'][:3]]
    data['disclaimer'] = 'Наблюдения для обсуждения, не клиническое заключение. Числа рассчитаны по сохранённым данным.'
    data['provider'] = settings().ai_provider
    report = Report(patient_id=patient_id, psychologist_id=psychologist_id, period_start=since, period_end=now(), report_data=jsonable_encoder(data))
    db.add(report)
    await db.flush()
    return report
