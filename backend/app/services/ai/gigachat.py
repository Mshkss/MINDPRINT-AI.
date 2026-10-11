import asyncio
import json
from gigachat import GigaChat
from app.core.config import settings
from app.services.ai.base import AIProvider, ProviderError, SYSTEM


class GigaChatProvider(AIProvider):
    async def chat(self, messages, context):
        cfg = settings()
        if not cfg.gigachat_credentials:
            raise ProviderError(
                "GigaChat не настроен. Укажите ключ на backend или выберите mock-режим."
            )
        try:
            async with GigaChat(
                credentials=cfg.gigachat_credentials,
                scope=cfg.gigachat_scope,
                model=cfg.gigachat_model,
                base_url=cfg.gigachat_base_url,
                verify_ssl_certs=True,
                ca_bundle_file=cfg.gigachat_ca_bundle,
                timeout=cfg.ai_timeout,
            ) as client:
                result = await asyncio.wait_for(
                    client.achat(
                        {
                            "messages": [
                                {
                                    "role": "system",
                                    "content": SYSTEM
                                    + "\nКонтекст: "
                                    + json.dumps(context, ensure_ascii=False),
                                },
                                *messages,
                            ]
                        }
                    ),
                    timeout=cfg.ai_timeout,
                )
                return result.choices[0].message.content
        except Exception as exc:
            raise ProviderError(
                "GigaChat временно недоступен. Попробуйте ещё раз или включите автономный режим."
            ) from exc

    async def analyze_entries(self, entries):
        answer = await self.chat(
            [{"role": "user", "content": json.dumps(entries, ensure_ascii=False)}],
            {
                "task": 'Верни только JSON {"observations":[{"entry_id":1,"topic":"Сон","evidence":"точная цитата из записи","observation":"осторожное наблюдение"}]}. Если оснований нет, верни пустой массив. Никаких диагнозов.'
            },
        )
        return json.loads(answer.strip().removeprefix("```json").removesuffix("```"))
