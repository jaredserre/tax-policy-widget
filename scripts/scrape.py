from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse, urldefrag

import feedparser
import requests
import yaml
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
SOURCES_FILE = ROOT / "sources.yml"
OUT_FILE = ROOT / "docs" / "stories.json"
MAX_PER_SOURCE = 25
MAX_TOTAL = 250

HEADERS = {
    "User-Agent": "TaxPolicyWidget/1.0 (+https://github.com/) Python requests",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

BAD_TITLE_PATTERNS = re.compile(r"^(home|about|contact|donate|subscribe|search|topics?|research|publications?|events?|staff|press)$", re.I)


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def normalize_url(url: str) -> str:
    url, _ = urldefrag(url)
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return url
    path = parsed.path.rstrip("/") or "/"
    return parsed._replace(path=path, query="").geturl()


def story_id(url: str) -> str:
    return hashlib.sha1(normalize_url(url).encode("utf-8")).hexdigest()[:16]


def parse_date(value: str | None) -> str | None:
    if not value:
        return None
    try:
        dt = parsedate_to_datetime(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    except Exception:
        pass
    try:
        from dateutil import parser
        dt = parser.parse(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    except Exception:
        return None


def include_url(url: str, src: dict) -> bool:
    u = normalize_url(url)
    parsed = urlparse(u)
    homepage_host = urlparse(src.get("homepage") or src["url"]).netloc.replace("www.", "")
    if parsed.netloc.replace("www.", "") != homepage_host:
        return False
    for token in src.get("exclude_url_contains", []) or []:
        if token in u:
            return False
    includes = src.get("include_url_contains", []) or []
    return not includes or any(token in u for token in includes)


def make_story(src: dict, title: str, url: str, published: str | None = None, summary: str | None = None) -> dict | None:
    title = clean_text(title)
    if len(title) < 12 or BAD_TITLE_PATTERNS.match(title):
        return None
    url = normalize_url(url)
    return {
        "id": story_id(url),
        "source_id": src["id"],
        "source": src["name"],
        "source_short": src.get("short", src["name"][:4].upper()),
        "title": title,
        "url": url,
        "published_at": published,
        "summary": clean_text(summary or ""),
        "first_seen_at": now_iso(),
    }


def fetch_rss(src: dict) -> list[dict]:
    feed = feedparser.parse(src["url"])
    out = []
    for entry in feed.entries[:MAX_PER_SOURCE]:
        url = entry.get("link")
        title = entry.get("title")
        if not url or not title:
            continue
        published = parse_date(entry.get("published") or entry.get("updated"))
        story = make_story(src, title, url, published, entry.get("summary"))
        if story:
            out.append(story)
    return out


def fetch_page(src: dict) -> list[dict]:
    resp = requests.get(src["url"], headers=HEADERS, timeout=25)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    candidates = []
    for a in soup.select("a[href]"):
        href = a.get("href")
        title = clean_text(a.get_text(" "))
        if not href or not title:
            continue
        url = normalize_url(urljoin(src["url"], href))
        if include_url(url, src):
            candidates.append((title, url))
    seen = set()
    out = []
    for title, url in candidates:
        sid = story_id(url)
        if sid in seen:
            continue
        seen.add(sid)
        story = make_story(src, title, url)
        if story:
            out.append(story)
        if len(out) >= MAX_PER_SOURCE:
            break
    return out


def load_existing() -> dict:
    if OUT_FILE.exists():
        try:
            return json.loads(OUT_FILE.read_text())
        except Exception:
            return {}
    return {}


def sort_key(story: dict) -> str:
    return story.get("published_at") or story.get("first_seen_at") or ""


def main() -> None:
    cfg = yaml.safe_load(SOURCES_FILE.read_text())
    existing = load_existing()
    by_id = {s["id"]: s for s in existing.get("stories", []) if "id" in s}
    errors = []
    counts = {}

    for src in cfg.get("sources", []):
        try:
            fresh = fetch_rss(src) if src.get("type") == "rss" else fetch_page(src)
            counts[src["id"]] = len(fresh)
            print(f"{src['name']}: {len(fresh)} stories")
            for story in fresh:
                if story["id"] in by_id:
                    old = by_id[story["id"]]
                    story["first_seen_at"] = old.get("first_seen_at") or story["first_seen_at"]
                    if not story.get("published_at"):
                        story["published_at"] = old.get("published_at")
                by_id[story["id"]] = story
        except Exception as exc:
            msg = f"{src.get('name', src.get('id'))}: {type(exc).__name__}: {exc}"
            print("ERROR", msg)
            errors.append(msg)
            counts[src.get("id", "unknown")] = 0

    stories = sorted(by_id.values(), key=sort_key, reverse=True)[:MAX_TOTAL]
    payload = {
        "updated_at": now_iso(),
        "sources": [{"id": s["id"], "name": s["name"], "short": s.get("short", s["name"][:4].upper()), "homepage": s.get("homepage", s.get("url"))} for s in cfg.get("sources", [])],
        "counts": counts,
        "errors": errors,
        "stories": stories,
    }
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
