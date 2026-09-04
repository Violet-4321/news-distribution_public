from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

from .news_collector import NewsCandidate, collect_news

STATE_FILE = Path(__file__).resolve().parent.parent / "state" / "notified_breaking.json"
STATE_TTL_DAYS = 14

BREAKING_GOOGLE_QUERIES = [
    "war OR invasion OR military strike OR attack when:1d",
    "missile OR nuclear OR escalation OR conflict when:1d",
    "coup OR martial law OR regime collapse when:1d",
    "major power OR NATO OR Russia OR China OR Iran military when:1d",
    "cyberattack OR catastrophic OR state of emergency when:1d",
]

BREAKING_GDELT_QUERIES = [
    "war OR invasion OR military strike",
    "missile OR nuclear OR escalation",
    "coup OR regime change OR martial law",
    "cyberattack OR emergency OR catastrophic",
]

GATE_SYSTEM_PROMPT = """You are a breaking-news gatekeeper for instant WeChat alerts. Your job is to catch only sudden, unambiguous, historically major international events, and to ignore everything else.

Flag ONLY events of this magnitude:
- A major power suddenly launches a war or a large-scale military attack (for example, a sudden US military strike on Iran).
- A nuclear or strategic missile incident with global consequences.
- An assassination or assassination attempt on a head of state, head of government, or other top political leader of a major power (for example, an assassination attempt on a US president).
- A sudden national political or constitutional crisis in a major country, such as martial law or a military takeover, a head of government being impeached or removed, a legislature stormed or seized, or the abrupt collapse of a government (for example, a sudden martial-law declaration, or a parliament crisis).
- The sudden collapse of a major government through a coup or regime change.
- A catastrophic global-scale cyberattack, terrorist attack, or disaster that dominates world headlines within hours.
- A sudden, unannounced breakdown of peace talks that immediately triggers a new major war.
Do NOT flag: routine diplomacy, ordinary elections, political scandals or court rulings, statements or warnings, isolated skirmishes, sanctions announcements, troop movements or mobilizations that have not led to attack, planned or widely anticipated actions, natural disasters below catastrophic scale, market news, celebrity news, or anything analysts describe as speculation. When in doubt, do NOT flag.
Return strict JSON only: {"events": [{"id": <input id>, "key": "short-stable-slug", "title": "...", "summary": "1-2 concise Chinese sentences on what happened and why it is major"}]}. Return empty list when nothing qualifies."""


@dataclass(frozen=True)
class BreakingEvent:
    key: str
    title: str
    summary: str
    url: str = ""


def main(hours: int = 3) -> None:
    load_dotenv()
    from openai import OpenAI

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY not set; skipping breaking-event check.")
        return

    candidates = collect_news(
        hours=hours,
        limit_per_source=25,
        google_queries=BREAKING_GOOGLE_QUERIES,
        gdelt_queries=BREAKING_GDELT_QUERIES,
    )
    recent = sorted(candidates, key=lambda c: c.published_at, reverse=True)[:60]
    print(f"Breaking candidates collected: {len(recent)}")
    if not recent:
        print("No candidates; nothing to check.")
        return

    compact = [
        {
            "id": index,
            "title": item.title,
            "source": item.source,
            "published_at": item.published_at.isoformat(),
            "url": item.url,
            "snippet": item.summary[:200],
        }
        for index, item in enumerate(recent)
    ]
    client = OpenAI(
        api_key=api_key,
        timeout=180,
        base_url=os.getenv("OPENAI_BASE_URL"),
    )
    model = os.getenv("OPENAI_MODEL", "deepseek-v4-flash")
    response = client.chat.completions.create(
        model=model,
        temperature=0.0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": GATE_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "Check the latest news candidates below for a qualifying major breaking event. "
                    "Return strict JSON with key 'events'.\n\n"
                    f"{json.dumps(compact, ensure_ascii=False)}"
                ),
            },
        ],
    )
    payload = json.loads(response.choices[0].message.content or "{}")
    events = _parse_events(payload.get("events", []), recent)

    state = _load_state()
    now = datetime.now(timezone.utc)
    fresh: list[BreakingEvent] = []
    for event in events:
        if event.key not in state:
            fresh.append(event)
            state[event.key] = now.isoformat()

    if fresh:
        from .wechat_push import push_wechat

        for event in fresh:
            content = f"{event.summary}\n来源链接：{event.url}" if event.url else event.summary
            pushed = push_wechat(title=f"【重大国际事件】{event.title}", content=content)
            print(f"Push event {event.key}: {'sent' if pushed else 'FAILED'}")
    else:
        print(f"No new qualifying major events (checked {len(events)} flagged, all previously notified).")

    _prune_state(state)
    _save_state(state)


def _parse_events(raw: list, candidates: list[NewsCandidate]) -> list[BreakingEvent]:
    by_id = {index: item for index, item in enumerate(candidates)}
    events: list[BreakingEvent] = []
    today = datetime.now(timezone.utc).date().isoformat()
    for item in raw[:5]:
        try:
            title = str(item.get("title", "")).strip()
            summary = str(item.get("summary", "")).strip()
            if not title or not summary:
                continue
            candidate = by_id.get(int(item.get("id", -1)))
            key = str(item.get("key") or "").strip()
            if not key:
                normalized = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
                key = f"{normalized[:60]}-{today}"
            events.append(
                BreakingEvent(
                    key=key,
                    title=title,
                    summary=summary,
                    url=candidate.url if candidate else "",
                )
            )
        except (KeyError, TypeError, ValueError, IndexError):
            continue
    return events


def _load_state() -> dict[str, str]:
    if not STATE_FILE.exists():
        return {}
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _prune_state(state: dict[str, str]) -> None:
    cutoff = (datetime.now(timezone.utc) - timedelta(days=STATE_TTL_DAYS)).isoformat()
    for key in [k for k, v in state.items() if v < cutoff]:
        state.pop(key, None)


def _save_state(state: dict[str, str]) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
