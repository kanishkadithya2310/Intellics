"""Intellics: helpers module (split out of app.py)."""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import html
import re
import threading

import streamlit as st

from config import GLOSS_PATTERNS, UTC


# ------------------------------------------------------------ text helpers
def clean_text(raw: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", raw or ""))).strip()


def md_safe(text: str) -> str:
    return re.sub(r"([\\`*_\[\]$~#<>|])", r"\\\1", text)


def small(text: str) -> str:
    """Small grey text for use inside markdown. HTML-escaped first, so a publisher name can never inject markup."""
    return f"<small>{md_safe(html.escape(text, quote=False))}</small>"


def safe_url(url: str) -> str:
    return url.replace(" ", "%20").replace(")", "%29").replace("(", "%28")


def sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) > 20]


def time_ago(ts: datetime | None) -> str:
    if not ts:
        return ""
    secs = max(0, int((datetime.now(UTC) - ts).total_seconds()))
    return ("just now" if secs < 60 else f"{secs // 60} min ago" if secs < 3600
            else f"{secs // 3600} h ago" if secs < 86400 else f"{secs // 86400} d ago")


def _stamp(now: datetime) -> str:
    """e.g. '14 Oct, 3:29 pm IST'. Expects a datetime already in IST."""
    return f"{now.day} {now:%b}, {now.hour % 12 or 12}:{now:%M} {'am' if now.hour < 12 else 'pm'} IST"


def glossary_hits(blob: str) -> list[tuple[str, str]]:
    return [(n, m) for n, p, m in GLOSS_PATTERNS if p.search(blob)]


# --------------------------------------------------- simple-language summaries
@st.cache_resource
def _store():
    return {"data": {}, "pending": set(), "lock": threading.Lock(), "pool": ThreadPoolExecutor(max_workers=2),
            "info_fail": {}, "nse_fail": {}}
