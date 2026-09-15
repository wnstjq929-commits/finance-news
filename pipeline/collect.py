"""출처별 피드를 모아 최근 N시간 기사 목록을 만든다."""
import html
import re
import time
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

import feedparser
import requests

from .sources import SOURCES, feed_urls

KST = timezone(timedelta(hours=9))
UA = "Mozilla/5.0 (compatible; FinNoteBot/1.0; +daily finance digest)"
TAG_RE = re.compile(r"<[^>]+>")


def clean(text):
    return re.sub(r"\s+", " ", html.unescape(TAG_RE.sub(" ", text or ""))).strip()


def parse_time(entry):
    for key in ("published_parsed", "updated_parsed"):
        t = entry.get(key)
        if t:
            return datetime(*t[:6], tzinfo=timezone.utc).astimezone(KST)
    for key in ("published", "updated", "pubDate"):
        raw = entry.get(key)
        if raw:
            try:
                dt = parsedate_to_datetime(raw)
                return (dt if dt.tzinfo else dt.replace(tzinfo=KST)).astimezone(KST)
            except (TypeError, ValueError):
                pass
    return None


def fetch(url, timeout=15):
    r = requests.get(url, headers={"User-Agent": UA}, timeout=timeout)
    r.raise_for_status()
    return feedparser.parse(r.content)


def strip_gnews_suffix(title, source_name):
    # 구글 뉴스 제목 끝의 " - 언론사명" 제거
    return re.sub(r"\s+-\s+[^-]{1,30}$", "", title).strip()


def collect(hours=24, now=None, log=print):
    now = now or datetime.now(KST)
    since = now - timedelta(hours=hours)
    articles, health = [], []

    for source in SOURCES:
        for feed in feed_urls(source):
            status = {"source": source["name"], "label": feed["label"],
                      "url": feed["url"], "kind": feed["kind"]}
            try:
                parsed = fetch(feed["url"])
                entries = parsed.entries or []
                kept = 0
                for e in entries:
                    published = parse_time(e)
                    if published and published < since:
                        continue
                    title = clean(e.get("title"))
                    if feed["kind"] == "gnews":
                        title = strip_gnews_suffix(title, source["name"])
                    if not title:
                        continue
                    articles.append({
                        "source_id": source["id"],
                        "source": source["name"],
                        "tier": source["tier"],
                        "source_score": source["score"],
                        "official": source["official"],
                        "title": title,
                        "summary": clean(e.get("summary") or e.get("description"))[:400],
                        "link": e.get("link"),
                        "published": published.isoformat() if published else None,
                        "feed": feed["label"],
                    })
                    kept += 1
                status.update(ok=True, entries=len(entries), kept=kept)
            except Exception as ex:  # 한 피드가 실패해도 전체는 계속
                status.update(ok=False, error=str(ex)[:160])
            health.append(status)
            log(f"  {'✓' if status.get('ok') else '✗'} {source['name']:<8} {feed['label']:<8} "
                f"{status.get('kept', 0)}건 {status.get('error', '')}")
            time.sleep(0.5)

    # 같은 링크 중복 제거
    seen, unique = set(), []
    for a in articles:
        key = a["link"] or a["title"]
        if key not in seen:
            seen.add(key)
            unique.append(a)
    return unique, health
