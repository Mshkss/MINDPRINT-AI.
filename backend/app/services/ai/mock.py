from app.services.ai.base import AIProvider

class MockProvider(AIProvider):
    async def chat(self, messages, context):
        content = messages[-1]['content'].lower()
        exercises = context.get('assignments', [])
        if exercises and any(w in content for w in ['трево','упражнен','работ','давай']):
            ex = exercises[0]
            return f'Похоже, сейчас непросто. Давай отделим то, что произошло, от предположений. В твоём плане есть упражнение «{ex["name"]}», назначенное психологом. Если готов, открой его кнопкой под разговором — пройдём шаги в твоём темпе.'
        if len(messages) > 1:
            return 'Спасибо, что поделился. Ты можешь рассказать подробнее: что в этой ситуации оказалось самым трудным? Я рядом, чтобы помочь тебе сформулировать переживания для следующей встречи с психологом.'
        return 'Я здесь, чтобы выслушать. Расскажи, что тебя сейчас занимает — можно начать с одного события или чувства. Мы можем просто поговорить или обратиться к упражнениям из твоего плана.'

    async def analyze_entries(self, entries):
        observations = []
        for e in entries:
            for topic, tokens in [('Сон',['сплю','сном','сон','бессон']), ('Работа',['работ','начальник']), ('Тревога',['трево','боюсь']), ('Общение',['друз','общени'])]:
                if any(t in e['content'].lower() for t in tokens):
                    observations.append({'entry_id':e['id'], 'topic':topic, 'evidence':e['content'], 'observation':f'В записи упоминается тема «{topic.lower()}». Гипотеза для обсуждения.'})
        return {'observations':observations[:100]}
