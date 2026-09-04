from __future__ import annotations

import os

import requests

from .summarizer import BriefContent
from .vix import VixSnapshot

SERVERCHAN_API = "https://sctapi.ftqq.com"
PUSHPLUS_API = "https://www.pushplus.plus/send"


def build_wechat_message(date_text: str, vix: VixSnapshot, brief: BriefContent) -> str:
    lines: list[str] = []
    lines.append(f"【每日简报】{date_text}")
    lines.append("")
    if vix.value is not None:
        lines.append(f"市场温度 | VIX: {vix.value:.1f} — {vix.interpretation}")
    else:
        lines.append(f"市场温度 | VIX: 暂无数据 — {vix.interpretation}")
    lines.append("")
    lines.append(f"今日摘要：{brief.trend_summary}")
    lines.append("")
    for index, story in enumerate(brief.stories, start=1):
        lines.append(f"{index}. {story.title}")
        if story.summary:
            lines.append(f"   {story.summary}")
        if story.why_it_matters:
            lines.append(f"   影响：{story.why_it_matters}")
        lines.append(f"   来源：{story.source}")
        lines.append("")
    return "\n".join(lines).strip()


def push_wechat(title: str, content: str) -> bool:
    try:
        sendkey = os.getenv("SERVERCHAN_SENDKEY")
        if sendkey:
            response = requests.post(
                f"{SERVERCHAN_API}/{sendkey}.send",
                data={"title": title, "desp": content},
                timeout=30,
            )
            response.raise_for_status()
            payload = response.json()
            if payload.get("code") != 0:
                print(f"WeChat push warning: {payload.get('message', payload)}")
                return False
            return True

        token = os.getenv("PUSHPLUS_TOKEN")
        if token:
            response = requests.post(
                PUSHPLUS_API,
                json={
                    "token": token,
                    "title": title,
                    "content": content,
                    "template": "txt",
                },
                timeout=30,
            )
            response.raise_for_status()
            payload = response.json()
            if payload.get("code") != 200:
                print(f"WeChat push warning: {payload.get('msg', 'unknown error')}")
                return False
            return True
        return False
    except Exception as exc:  # noqa: BLE001 - push must never break the pipeline
        print(f"WeChat push failed: {exc}")
        return False
