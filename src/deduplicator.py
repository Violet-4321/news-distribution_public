from __future__ import annotations

import re
from difflib import SequenceMatcher

from .news_collector import NewsCandidate


NOISE_KEYWORDS = {
    "celebrity",
    "movie",
    "music",
    "sports",
    "football",
    "basketball",
    "gaming patch",
    "changelog",
    "release notes",
    "minor update",
}

SIGNAL_KEYWORDS = {
    "ai",
    "ai pc",
    "ai agent",
    "artificial intelligence",
    "openai",
    "anthropic",
    "deepmind",
    "earnings",
    "consumer price index",
    "cpi",
    "employment situation",
    "fomc",
    "google",
    "guidance",
    "ipo",
    "markets",
    "microsoft",
    "nvidia",
    "profit",
    "producer price index",
    "ppi",
    "payroll employment",
    "revenue",
    "rtx spark",
    "stocks",
    "semiconductor",
    "chip",
    "gpu",
    "tsmc",
    "asml",
    "china",
    "u.s.",
    "us-china",
    "china-us",
    "united states",
    "tariff",
    "sanction",
    "export control",
    "entity list",
    "fed",
    "federal reserve",
    "inflation",
    "unemployment rate",
    "rates",
    "interest rate",
    "rate cut",
    "rate hike",
    "gdp",
    "yuan",
    "treasury",
    "huawei",
    "alibaba",
    "tencent",
    "byd",
}


def filter_and_deduplicate(candidates: list[NewsCandidate]) -> list[NewsCandidate]:
    filtered = [item for item in candidates if _passes_basic_filter(item)]
    deduped: list[NewsCandidate] = []
    seen_urls: set[str] = set()
    seen_titles: list[str] = []

    for item in sorted(filtered, key=lambda candidate: candidate.published_at, reverse=True):
        normalized_url = item.url.split("?")[0].rstrip("/")
        normalized_title = _normalize_title(item.title)
        if not normalized_title or normalized_url in seen_urls:
            continue
        if any(_is_similar(normalized_title, existing) for existing in seen_titles):
            continue
        deduped.append(item)
        seen_urls.add(normalized_url)
        seen_titles.append(normalized_title)

    return deduped


def _passes_basic_filter(item: NewsCandidate) -> bool:
    text = f"{item.title} {item.summary}".lower()
    if not item.title or not item.url:
        return False
    has_signal = any(_contains_term(text, keyword) for keyword in SIGNAL_KEYWORDS)
    if any(_contains_term(text, keyword) for keyword in NOISE_KEYWORDS):
        return has_signal
    return has_signal


def _normalize_title(title: str) -> str:
    title = title.lower()
    title = re.sub(r"[^a-z0-9\u4e00-\u9fff ]+", " ", title)
    return " ".join(title.split())


def _is_similar(left: str, right: str) -> bool:
    return SequenceMatcher(None, left, right).ratio() >= 0.82


def _contains_term(text: str, term: str) -> bool:
    if not term.isascii():
        return term in text
    pattern = r"(?<![a-z0-9])" + re.escape(term) + r"(?![a-z0-9])"
    return re.search(pattern, text) is not None
