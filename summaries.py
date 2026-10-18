"""Intellics: summaries module (split out of app.py)."""
from __future__ import annotations
import json
import time
from concurrent.futures import wait

import requests
import streamlit as st

from config import GROQ_MODEL, GROQ_URL, SUMMARY_WAIT, SYSTEM_PROMPT, TOPIC_WHY, log
from helpers import _store, glossary_hits, sentences


def groq_key() -> str:
    try:
        return st.secrets.get("GROQ_API_KEY", "") or ""
    except Exception:
        return ""


def basic_summary(s: dict) -> str:
    """No-AI fallback: always gives 3-4 plain sentences, so no article is left without a summary."""
    blob = f"{s['title']} {s['summary']}"
    items = [f"{s['title'].rstrip('.!?')}."]
    extras = [x[:220] for x in sentences(s["summary"])[:2]] + [f"{n} means {m}." for n, m in glossary_hits(blob)[:2]]
    items += extras[:2]
    items.append(TOPIC_WHY[s["topics"][0]])
    if len(items) < 3:
        items.insert(1, "Open the full article to read all the details.")
    return " ".join(items[:4])


def _run_batch(batch: list[dict], api_key: str) -> None:
    lines = [f"{i}. HEADLINE: {s['title']}\n   SNIPPET: {s['summary'][:400] or '(none)'}" for i, s in enumerate(batch, 1)]
    body = {"model": GROQ_MODEL, "temperature": 0.3, "max_tokens": 1500, "response_format": {"type": "json_object"},
            "messages": [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": "\n".join(lines)}]}
    result: dict = {}
    for _ in range(2):
        try:
            r = requests.post(GROQ_URL, headers={"Authorization": f"Bearer {api_key}"}, json=body, timeout=30)
            if r.status_code == 429:
                time.sleep(min(float(r.headers.get("retry-after", 8)), 20))
                continue
            r.raise_for_status()
            result = json.loads(r.json()["choices"][0]["message"]["content"])
            break
        except Exception as exc:
            log.warning("AI summary batch failed: %s", exc)  # never log the key or the request headers
            break
    store = _store()
    with store["lock"]:
        for i, s in enumerate(batch, 1):
            text = str(result.get(str(i), "")).strip()
            if 100 <= len(text) <= 900:  # too short or rambling answers are ignored; the basic summary stays
                store["data"][s["id"]] = {"t": text, "m": "ai", "at": time.time()}
            store["pending"].discard(s["id"])


def get_summaries(stories: list[dict]) -> dict[str, dict]:
    """Returns a summary for every story straight away (basic ones where AI is not ready yet).
    AI batches keep running in the background; whatever finishes shows up on the next refresh."""
    store, api_key, now, todo = _store(), groq_key(), time.time(), []
    with store["lock"]:
        if len(store["data"]) > 1500:
            for k in sorted(store["data"], key=lambda k: store["data"][k]["at"])[:300]:
                store["data"].pop(k)
        for s in stories:
            entry = store["data"].get(s["id"])
            is_new = entry is None
            if is_new:
                entry = store["data"][s["id"]] = {"t": basic_summary(s), "m": "basic", "at": now}
            if api_key and entry["m"] == "basic" and s["id"] not in store["pending"] and (is_new or now - entry["at"] > 600):
                todo.append(s)
                store["pending"].add(s["id"])
                entry["at"] = now
    futures = [store["pool"].submit(_run_batch, todo[i:i + 5], api_key) for i in range(0, len(todo), 5)]
    if futures:
        wait(futures, timeout=SUMMARY_WAIT)  # slow batches keep running and show up on the next refresh
    with store["lock"]:
        return {s["id"]: dict(store["data"][s["id"]]) for s in stories}
