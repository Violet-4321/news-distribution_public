from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from html.parser import HTMLParser
from typing import Iterable
from urllib.parse import quote_plus

import feedparser
import requests


@dataclass(frozen=True)
class NewsCandidate:
    title: str
    url: str
    source: str
    published_at: datetime
    summary: str = ""


GOOGLE_NEWS_QUERIES = [
    "artificial intelligence industry OR AI regulation OR AI policy when:1d",
    "frontier AI model OR artificial intelligence breakthrough when:1d",
    "AI data center OR AI capex OR AI investment when:1d",
    "AI chip OR semiconductor industry when:1d",
    "central bank OR monetary policy OR interest rate when:1d",
    "global economy OR economic outlook OR GDP growth when:1d",
    "inflation OR recession OR fiscal policy when:1d",
    "trade policy OR tariff OR export control when:1d",
    "China economy OR China monetary policy OR China economic policy when:1d",
    "stock market OR global markets OR market outlook when:1d",
    "military OR defense OR armed conflict OR war when:1d",
    "geopolitics OR diplomacy OR summit OR international relations when:1d",
    "sanctions OR treaty OR national security when:1d",
    "China US OR Russia Ukraine OR Middle East OR Taiwan OR North Korea when:1d",
]

GDELT_QUERIES = [
    "artificial intelligence industry OR AI policy",
    "global economy OR economic outlook",
    "central bank OR monetary policy",
    "inflation OR interest rate OR recession",
    "trade OR tariff OR export control",
    "China economy OR China economic policy",
    "AI chips OR semiconductor industry",
    "military OR defense OR armed conflict",
    "geopolitics OR diplomacy OR sanctions",
]

FED_MONETARY_RSS_URL = "https://www.federalreserve.gov/feeds/press_monetary.xml"
BLS_MAJOR_RELEASE_FEEDS = {
    "Employment Situation": "https://www.bls.gov/feed/empsit.rss",
    "Consumer Price Index": "https://www.bls.gov/feed/cpi.rss",
    "Producer Price Index": "https://www.bls.gov/feed/ppi.rss",
}
RSS_REQUEST_HEADERS = {
    "User-Agent": "daily-news-brief/1.0 (public RSS collector)",
}


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def collect_news(hours: int = 24, limit_per_source: int = 50) -> list[NewsCandidate]:
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    candidates: list[NewsCandidate] = []
    candidates.extend(_collect_google_news(since, limit_per_source))
    candidates.extend(_collect_gdelt(since, limit_per_source))
    candidates.extend(_collect_fed_monetary_news(since, limit_per_source))
    candidates.extend(_collect_bls_major_releases(since, limit_per_source))
    return [item for item in candidates if item.published_at >= since]


def _collect_google_news(since: datetime, limit_per_query: int) -> list[NewsCandidate]:
    items: list[NewsCandidate] = []
    for query in GOOGLE_NEWS_QUERIES:
        encoded = quote_plus(query)
        url = (
            "https://news.google.com/rss/search?"
            f"q={encoded}&hl=en-US&gl=US&ceid=US:en"
        )
        feed = feedparser.parse(url)
        for entry in feed.entries[:limit_per_query]:
            published_at = _parse_feed_datetime(
                getattr(entry, "published", None) or getattr(entry, "updated", None)
            )
            if not published_at or published_at < since:
                continue
            title, source = _split_google_title(_clean_text(getattr(entry, "title", "")))
            items.append(
                NewsCandidate(
                    title=title,
                    url=getattr(entry, "link", ""),
                    source=source,
                    published_at=published_at,
                    summary=_clean_text(getattr(entry, "summary", "")),
                )
            )
    return items


def _collect_gdelt(since: datetime, limit_per_query: int) -> list[NewsCandidate]:
    items: list[NewsCandidate] = []
    start = since.strftime("%Y%m%d%H%M%S")
    end = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    for query in GDELT_QUERIES:
        params = {
            "query": query,
            "mode": "ArtList",
            "format": "json",
            "maxrecords": str(limit_per_query),
            "sort": "HybridRel",
            "startdatetime": start,
            "enddatetime": end,
        }
        try:
            response = requests.get(
                "https://api.gdeltproject.org/api/v2/doc/doc",
                params=params,
                timeout=20,
            )
            response.raise_for_status()
        except requests.RequestException:
            continue

        try:
            payload = response.json()
        except ValueError:
            continue

        for article in payload.get("articles", []):
            published_at = _parse_gdelt_datetime(article.get("seendate"))
            if not published_at or published_at < since:
                continue
            items.append(
                NewsCandidate(
                    title=_clean_text(article.get("title", "")),
                    url=article.get("url", ""),
                    source=article.get("domain") or "GDELT",
                    published_at=published_at,
                    summary="",
                )
            )
    return items


def _collect_fed_monetary_news(
    since: datetime,
    limit: int,
) -> list[NewsCandidate]:
    entries = _fetch_rss_entries(FED_MONETARY_RSS_URL)
    items: list[NewsCandidate] = []
    for entry in entries[:limit]:
        title = _clean_text(getattr(entry, "title", ""))
        if not _is_major_fed_release(title):
            continue
        candidate = _rss_entry_to_candidate(entry, "Federal Reserve")
        if candidate and candidate.published_at >= since:
            items.append(candidate)
    return items


def _collect_bls_major_releases(
    since: datetime,
    limit_per_feed: int,
) -> list[NewsCandidate]:
    items: list[NewsCandidate] = []
    for release_name, url in BLS_MAJOR_RELEASE_FEEDS.items():
        entries = _fetch_rss_entries(url)
        for entry in entries[:limit_per_feed]:
            title = _clean_text(getattr(entry, "title", ""))
            if not _is_major_bls_release(release_name, title):
                continue
            candidate = _rss_entry_to_candidate(entry, "U.S. Bureau of Labor Statistics")
            if candidate and candidate.published_at >= since:
                items.append(candidate)
    return items


def _fetch_rss_entries(url: str) -> list:
    try:
        response = requests.get(
            url,
            headers=RSS_REQUEST_HEADERS,
            timeout=20,
        )
        response.raise_for_status()
    except requests.RequestException:
        return []
    return list(feedparser.parse(response.content).entries)


def _rss_entry_to_candidate(entry, source: str) -> NewsCandidate | None:
    published_at = _parse_feed_datetime(
        getattr(entry, "published", None) or getattr(entry, "updated", None)
    )
    title = _clean_text(getattr(entry, "title", ""))
    url = getattr(entry, "link", "")
    if not published_at or not title or not url:
        return None
    return NewsCandidate(
        title=title,
        url=url,
        source=source,
        published_at=published_at,
        summary=_clean_text(getattr(entry, "summary", "")),
    )


def _is_major_fed_release(title: str) -> bool:
    text = title.lower()
    if "minutes" in text:
        return False
    return any(
        term in text
        for term in (
            "fomc statement",
            "monetary policy report",
            "emergency",
            "liquidity facility",
            "federal funds rate",
            "discount rate",
        )
    )


def _is_major_bls_release(release_name: str, title: str) -> bool:
    text = title.lower()
    if release_name == "Employment Situation":
        payroll_change = _extract_number(
            text,
            r"payroll employment .*? by ([\d,]+)",
        )
        return (
            payroll_change is not None
            and payroll_change >= 200_000
        ) or any(
            term in text
            for term in (
                "payroll employment declines",
                "payroll employment decreases",
                "unemployment rate rises",
                "unemployment rate increases",
            )
        )

    monthly_change = _extract_number(
        text,
        r"(?:rises|increases|advances|falls|declines|decreases) ([\d.]+)%",
    )
    if monthly_change is None:
        return False
    if any(term in text for term in ("falls", "declines", "decreases")):
        return True
    threshold = 0.4 if release_name == "Consumer Price Index" else 0.5
    return monthly_change >= threshold


def _extract_number(text: str, pattern: str) -> float | None:
    match = re.search(pattern, text)
    if not match:
        return None
    return float(match.group(1).replace(",", ""))


def _parse_feed_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _parse_gdelt_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    for fmt in ("%Y%m%dT%H%M%SZ", "%Y%m%d%H%M%S"):
        try:
            return datetime.strptime(value, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def _clean_text(value: str) -> str:
    parser = _HTMLTextExtractor()
    parser.feed(value)
    text = unescape(" ".join(parser.parts))
    return " ".join(text.replace("\n", " ").split())


def _split_google_title(title: str) -> tuple[str, str]:
    if " - " not in title:
        return title, "Google News"
    story_title, source = title.rsplit(" - ", 1)
    return story_title.strip() or title, source.strip() or "Google News"


def candidates_to_dicts(candidates: Iterable[NewsCandidate]) -> list[dict[str, str]]:
    return [
        {
            "title": item.title,
            "url": item.url,
            "source": item.source,
            "published_at": item.published_at.isoformat(),
            "summary": item.summary,
        }
        for item in candidates
    ]
