"""Intellics: news page module (split out of app.py)."""
from __future__ import annotations
from datetime import datetime

import streamlit as st

from config import IST, MAX_STORIES, NEWS_REFRESH, SOURCES
from helpers import _stamp, glossary_hits, md_safe, safe_url, small, time_ago
from news import load_news
from prices import load_prices
from summaries import get_summaries


# ---------------------------------------------------------------- filters
def init_state() -> None:
    for k, v in {"query": "", "today_only": False, "sources": list(SOURCES)}.items():
        st.session_state.setdefault(k, v)
    # drop any source that is no longer in the trusted list (a visitor's old session may still hold it)
    st.session_state["sources"] = [s for s in st.session_state["sources"] if s in SOURCES]


def reset_filters() -> None:
    st.session_state.update(topic="All", query="", today_only=False, sources=list(SOURCES))


def refresh_all() -> None:
    load_news.clear()
    load_prices.clear()


def filter_bar() -> None:
    st.text_input("Search", key="query", placeholder="🔎 Search headlines, e.g. RBI, Reliance, gold", label_visibility="collapsed")
    with st.expander("More filters"):
        st.toggle("Only today's stories", key="today_only")
        st.multiselect("Sources", list(SOURCES), key="sources")
        a, b = st.columns(2)
        a.button("🔄 Refresh now", on_click=refresh_all)
        b.button("Reset filters", on_click=reset_filters)


def apply_filters(stories: list[dict]) -> list[dict]:
    ss, today = st.session_state, datetime.now(IST).date()
    topic, q, out = ss.get("topic") or "All", ss["query"].strip().lower(), []
    for s in stories:
        if s["feed"] not in ss["sources"] or (topic != "All" and topic not in s["topics"]):
            continue
        if ss["today_only"] and (not s["ts"] or s["ts"].astimezone(IST).date() != today):
            continue
        if q and q not in f"{s['title']} {s['summary']} {' '.join(s['tags'])}".lower():
            continue
        out.append(s)
    return out


# --------------------------------------------------------------------- tabs
def story_time(ts: datetime | None) -> str:
    """'24 min ago · 14 Oct, 3:20 pm IST', or an honest 'not provided' when the feed gave no time."""
    if not ts:
        return "publication time not provided by the source"
    return f"{time_ago(ts)} · {_stamp(ts.astimezone(IST))}"


def render_story(s: dict, summ: dict) -> None:
    with st.container(border=True, key=f"card_{s['id']}"):
        st.markdown(f"**[{md_safe(s['title'])}]({safe_url(s['link'])})**")
        st.markdown(" ".join(f":blue-badge[{t}]" for t in s["topics"][:2]) + "  \n" + small(f"{s['source']} · {story_time(s['ts'])}"),
                    unsafe_allow_html=True)
        st.markdown(md_safe(summ["t"]))
        if s["tags"]:
            st.caption("Companies in this story: " + ", ".join(s["tags"]))
        terms = glossary_hits(f"{s['title']} {s['summary']}")
        if terms:
            with st.expander("📖 Words explained"):
                for name, meaning in terms:
                    st.markdown(f"**{md_safe(name)}**: {md_safe(meaning)}")
        st.link_button("Read full article ↗", s["link"])


def news_tab(items: list[dict], total: int) -> None:
    if not items:
        st.info("No stories match your filters.")
        st.button("Reset filters", on_click=reset_filters, key="reset_empty")
        return
    with st.spinner("Loading summaries…"):
        summaries = get_summaries(items)
    for s in items:
        render_story(s, summaries[s["id"]])


@st.fragment(run_every=f"{NEWS_REFRESH}s")
def news_section() -> None:
    stories, failed, fetched_at = load_news()
    st.caption(f"News updated {fetched_at:%H:%M:%S} IST · refreshes every {NEWS_REFRESH // 60} min · trusted sources only")
    if not stories:
        st.error("Couldn't load any news right now. Please tap Refresh now in a minute.")
        st.button("🔄 Refresh now", on_click=refresh_all, key="retry_news")
        return
    news_tab(apply_filters(stories)[:MAX_STORIES], len(stories))
