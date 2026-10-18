"""Intellics: news module (split out of app.py)."""
from __future__ import annotations
from difflib import SequenceMatcher
from concurrent.futures import ThreadPoolExecutor, wait
from datetime import datetime
import hashlib
import re
import time

import feedparser
import requests
import streamlit as st

from config import FEED_DEADLINE, GOOGLE_SOURCES, HEADERS, IST, NEWS_REFRESH, PATTERNS, SOURCES, TOPIC_PATTERNS, UTC, log, trusted_publisher
from helpers import clean_text


# --------------------------------------------------------------- news data
def build_story(entry, source: str) -> dict | None:
    title, link = clean_text(entry.get("title", "")), (entry.get("link", "") or "").strip()
    if not title or not re.match(r"^https?://", link, re.I):  # security: only normal web links, never javascript: etc.
        return None
    shown = source
    if source in GOOGLE_SOURCES and " - " in title:
        title, publisher = title.rsplit(" - ", 1)
        if source == "Google News":
            if not trusted_publisher(publisher):  # keep only reputable publishers
                return None
            shown = f"Google News ({publisher.strip()})"
    elif source == "Google News":
        return None  # no publisher name, so we cannot vouch for it
    summary = clean_text(entry.get("summary") or entry.get("description") or "")
    if summary.lower().startswith(title.lower()[:40]) or SequenceMatcher(None, summary.lower(), title.lower()).ratio() > 0.8:
        summary = ""
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    blob = f"{title} {summary}"
    tags = [n for n, pats in PATTERNS.items() if any(p.search(blob) for p in pats)]
    topics = [t for t, p in TOPIC_PATTERNS.items() if p.search(blob)]
    if tags and "Companies" not in topics:
        topics.append("Companies")
    return {"id": hashlib.md5((link + title).encode()).hexdigest()[:12], "title": title, "link": link,
            "source": shown, "feed": source, "summary": summary, "tags": tags, "topics": topics or ["Markets"],
            "ts": datetime(*parsed[:6], tzinfo=UTC) if parsed else None}


def http_get(url: str, headers: dict | None = None, timeout: int = 6) -> requests.Response:
    """GET with a timeout and ONE retry (after a short pause) for timeouts, connection errors, 429 and 5xx.
    Other errors (404, 403...) fail straight away, because retrying would not help."""
    for attempt in (0, 1):
        try:
            resp = requests.get(url, headers=headers or HEADERS, timeout=timeout)
            if (resp.status_code == 429 or resp.status_code >= 500) and attempt == 0:
                time.sleep(0.8)
                continue
            resp.raise_for_status()
            return resp
        except (requests.Timeout, requests.ConnectionError):
            if attempt == 1:
                raise
            time.sleep(0.8)
    raise RuntimeError("request failed")


def fetch_feed(item):
    """item = (source name, list of feed URLs). Tries each URL in order until one gives stories."""
    name, urls = item
    err = "no stories found"
    for url in urls:
        try:
            entries = feedparser.parse(http_get(url).content).entries
            if entries:
                return name, entries, None
        except Exception as exc:
            err = str(exc)
            log.warning("Feed failed: %s %s (%s)", name, url, exc)
    return name, [], err


def dedupe(stories: list[dict]) -> list[dict]:
    """Drop repeats: same link, same normalised headline, or a headline sharing 75%+ of its words with one already kept."""
    norm = lambda t: re.sub(r"[^a-z0-9 ]", "", t.lower())
    kept, links, keys, word_sets = [], set(), set(), []
    for s in stories:
        key = norm(s["title"])
        words = frozenset(key.split())
        if s["link"] in links or key in keys:
            continue
        if words and any(len(words & w) / len(words | w) >= 0.75 for w in word_sets):
            continue
        links.add(s["link"])
        keys.add(key)
        word_sets.append(words)
        kept.append(s)
    return kept


@st.cache_data(ttl=NEWS_REFRESH, show_spinner=False)
def load_news():
    """All feeds are read in parallel. Feeds that are still silent after FEED_DEADLINE seconds are skipped
    (and reported as 'did not respond'), so one slow website cannot freeze the whole page."""
    stories, failed = [], []
    pool = ThreadPoolExecutor(max_workers=8)
    futures = {name: pool.submit(fetch_feed, (name, urls)) for name, urls in SOURCES.items()}
    wait(list(futures.values()), timeout=FEED_DEADLINE)
    pool.shutdown(wait=False, cancel_futures=True)
    for name, fut in futures.items():
        if not fut.done():
            failed.append(name)
            continue
        try:
            _, entries, err = fut.result()
        except Exception as exc:
            log.warning("Feed crashed: %s (%s)", name, exc)
            failed.append(name)
            continue
        if err:
            failed.append(name)
        stories += [s for s in (build_story(e, name) for e in entries) if s]
    stories.sort(key=lambda s: s["ts"] or datetime.min.replace(tzinfo=UTC), reverse=True)
    return dedupe(stories)[:200], failed, datetime.now(IST)
