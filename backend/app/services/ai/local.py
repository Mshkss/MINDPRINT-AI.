import json
import httpx
from app.core.config import settings
from app.services.ai.base import AIProvider, ProviderError, SYSTEM

class LocalLLMProvider(AIProvider):
    async def chat(self, messages, context):
        cfg = settings()
        try:
            async with httpx.AsyncClient(timeout=cfg.ai_timeout) as client:
                response = await client.post(cfg.local_llm_url.rstrip('/')+'/chat/completions', json={'model':cfg.local_llm_model,'messages':[{'role':'system','content':SYSTEM+'\n'+json.dumps(context,ensure_ascii=False)},*messages], 'temperature':0.4})
                response.raise_for_status()
                return response.json()['choices'][0]['message']['content']
        except Exception as exc:
            raise ProviderError('Локальная модель недоступна. Проверьте сервер инференса.') from exc
    async def analyze_entries(self, entries):
        answer = await self.chat([{'role':'user','content':json.dumps(entries,ensure_ascii=False)}], {'task':'Верни JSON observations: массив {entry_id, topic, evidence (дословная цитата), observation}. Без диагнозов. Нет оснований — пустой массив.'})
        return json.loads(answer.strip().removeprefix('```json').removesuffix('```'))
