from functools import lru_cache

import anthropic

from app.core.config import get_settings
from app.core.errors import AssistantUnavailableError
from app.schema.assistant import AssistantQueryPlan

MODEL = "claude-haiku-4-5"

SYSTEM_PROMPT = """你是 Manga Record 的收藏助理，把使用者的自然語言問題轉成查詢條件，用來查詢「目前登入者自己的漫畫收藏」。

可用欄位：
- statuses：plan_to_read(待看) / reading(追讀中) / dropped(棄坑) / completed(已追完)，可複選，不篩選就設 null；「還沒看完」通常對應 [plan_to_read, reading]
- categories：hot_blooded(熱血) / mystery(懸疑) / adventure(冒險) / romance(愛情) / casual(輕鬆) / competition(競技) / revenge(復仇) / slice_of_life(生活) / other(其他)，可複選，不篩選就設 null
- min_rating / max_rating：1-5，沒評分過的收藏不會被篩到
- sort_by：rating / last_read_at / current_chapter / created_at
- sort_order：asc / desc
- limit：預設 20，最多 50

如果問題跟使用者自己的漫畫收藏無關（例如問天氣、閒聊、問別人的收藏），answerable 設 false。
summary 永遠用一句繁體中文簡短複述你理解的查詢或說明為什麼無法回答，這句話會直接顯示給使用者看。"""


@lru_cache
def _client() -> anthropic.Anthropic:
    settings = get_settings()
    if not settings.anthropic_api_key:
        raise AssistantUnavailableError("AI assistant is not configured")
    return anthropic.Anthropic(api_key=settings.anthropic_api_key)


def plan_query(question: str) -> AssistantQueryPlan:
    client = _client()
    try:
        response = client.messages.parse(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": question}],
            output_format=AssistantQueryPlan,
        )
    except anthropic.APIConnectionError as exc:
        raise AssistantUnavailableError("AI assistant is temporarily unavailable") from exc
    except anthropic.APIStatusError as exc:
        raise AssistantUnavailableError("AI assistant is temporarily unavailable") from exc

    plan = response.parsed_output
    if plan is None:
        raise AssistantUnavailableError("AI assistant did not return a usable response")
    return plan
