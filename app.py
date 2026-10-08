"""Intellics: Indian markets news dashboard (beta polish release).

Same features as before (metrics, News / Top gainers & losers / Stocks in focus,
sidebar filters, auto-refresh). Changes are fixes and hardening only.
"""
from __future__ import annotations

import html
import logging
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from difflib import SequenceMatcher
from zoneinfo import ZoneInfo

import feedparser
import requests
import streamlit as st
import yfinance as yf

# ----------------------------------------------------------------- settings
VERSION = "0.9 beta"
REFRESH_SECONDS = 120
MAX_STORIES = 40
FEEDBACK_URL = ""  # paste your Google Form link here to show the feedback button
IST = ZoneInfo("Asia/Kolkata")
UTC = timezone.utc
HEADERS = {"User-Agent": "Mozilla/5.0 (Intellics beta; learning project)"}

# Replace these with the feed URLs already used in your app if they differ.
SOURCES = {
    "Economic Times": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "Moneycontrol": "https://www.moneycontrol.com/rss/MCtopnews.xml",
    "Mint": "https://www.livemint.com/rss/markets",
    "Business Standard": "https://www.business-standard.com/rss/markets-106.rss",
    "BusinessLine": "https://www.thehindubusinessline.com/markets/feeder/default.rss",
    "Google News": "https://news.google.com/rss/search?q=Sensex+OR+Nifty+OR+RBI+when:1d&hl=en-IN&gl=IN&ceid=IN:en",
}

INDICES = {
    "Sensex": "^BSESN",
    "Nifty 50": "^NSEI",
    "Brent crude (USD/bbl)": "BZ=F",
    "Gold (USD/oz)": "GC=F",
}

# name -> (Yahoo ticker, aliases as regex). Short ALL-CAPS aliases match case-sensitively.
COMPANIES = {
    "TCS": ("TCS.NS", ["TCS", "Tata Consultancy"]),
    "Infosys": ("INFY.NS", ["Infosys"]),
    "HCL Tech": ("HCLTECH.NS", ["HCL Tech", "HCLTech", "HCL Technologies"]),
    "Wipro": ("WIPRO.NS", ["Wipro"]),
    "Tech Mahindra": ("TECHM.NS", ["Tech Mahindra"]),
    "Reliance": ("RELIANCE.NS", ["Reliance(?! on\\b)"]),
    "HDFC Bank": ("HDFCBANK.NS", ["HDFC Bank"]),
    "ICICI Bank": ("ICICIBANK.NS", ["ICICI Bank"]),
    "SBI": ("SBIN.NS", ["SBI(?! Life| Cards)", "State Bank of India"]),
    "SBI Life": ("SBILIFE.NS", ["SBI Life"]),
    "Kotak Bank": ("KOTAKBANK.NS", ["Kotak Mahindra Bank", "Kotak Bank"]),
    "Axis Bank": ("AXISBANK.NS", ["Axis Bank"]),
    "ITC": ("ITC.NS", ["ITC(?! Hotels)"]),
    "L&T": ("LT.NS", ["Larsen", "L&T"]),
    "Tata Motors": ("TATAMOTORS.NS", ["Tata Motors"]),
    "Tata Steel": ("TATASTEEL.NS", ["Tata Steel"]),
    "Tata Power": ("TATAPOWER.NS", ["Tata Power"]),
    "Adani Ports": ("ADANIPORTS.NS", ["Adani Ports"]),
    "Adani Enterprises": ("ADANIENT.NS", ["Adani Enterprises"]),
    "Airtel": ("BHARTIARTL.NS", ["Airtel"]),
    "Maruti": ("MARUTI.NS", ["Maruti"]),
    "M&M": ("M&M.NS", ["M&M", "Mahindra & Mahindra"]),
    "Sun Pharma": ("SUNPHARMA.NS", ["Sun Pharma"]),
    "HUL": ("HINDUNILVR.NS", ["Hindustan Unilever", "HUL"]),
    "Asian Paints": ("ASIANPAINT.NS", ["Asian Paints"]),
    "Bajaj Finance": ("BAJFINANCE.NS", ["Bajaj Finance"]),
    "Titan": ("TITAN.NS", ["Titan"]),
    "JSW Steel": ("JSWSTEEL.NS", ["JSW Steel"]),
    "ONGC": ("ONGC.NS", ["ONGC"]),
    "NTPC": ("NTPC.NS", ["NTPC"]),
    "Power Grid": ("POWERGRID.NS", ["Power Grid"]),
    "Coal India": ("COALINDIA.NS", ["Coal India"]),
    "BEL": ("BEL.NS", ["BEL", "Bharat Electronics"]),
    "Polycab": ("POLYCAB.NS", ["Polycab"]),
}

TOPICS = {
    "Markets": ["sensex", "nifty", "stock market", "shares", "stocks", "bse", "nse", "ipo", "sebi", "fii", "fpi"],
    "Economy & RBI": ["rbi", "repo", "inflation", "gdp", "rate hike", "rate cut", "fiscal", "budget", "rupee", "economy", "gst"],
    "Companies": ["results", "earnings", "profit", "revenue", "acquisition", "merger", "ceo", "block deal", "order win"],
    "Global": ["fed", "treasury", "wall street", "china", "global", "dollar", "europe", "asia", "emerging market"],
    "Commodities": ["crude", "brent", "oil", "gold", "silver", "commodity", "opec", "natural gas", "copper"],
}

log = logging.getLogger("intellics")
logging.basicConfig(level=logging.INFO)

st.set_page_config(page_title="Intellics", page_icon="📈", layout="wide",
                   initial_sidebar_state="collapsed")  # keeps the sidebar off the content on phones


def _compile(alias: str) -> re.Pattern:
    base = alias.split("(")[0]
    flags = 0 if base.isupper() and len(base) <= 5 else re.I
    return re.compile(rf"(?<![A-Za-z0-9]){alias}(?![A-Za-z0-9])", flags)


PATTERNS = {n: [_compile(a) for a in als] for n, (_, als) in COMPANIES.items()}
TOPIC_PATTERNS = {t: re.compile(r"\b(" + "|".join(map(re.escape, kw)) + r")\b", re.I) for t, kw in TOPICS.items()}


# ------------------------------------------------------------ text helpers
def clean_text(raw: str) -> str:
    """Strip HTML tags/entities left over from RSS summaries."""
    text = html.unescape(re.sub(r"<[^>]+>", " ", raw or ""))
    return re.sub(r"\s+", " ", text).strip()


def md_safe(text: str) -> str:
    """Escape characters Streamlit would treat as markdown/LaTeX (fixes the $ glitch)."""
    return re.sub(r"([\\`*_\[\]$~#<>|])", r"\\\1", text)


def trim(text: str, limit: int) -> str:
    """Cut at a sentence or word boundary instead of mid-word."""
    if len(text) <= limit:
        return text
    cut = text[:limit]
    stop = max(cut.rfind(". "), cut.rfind("? "), cut.rfind("! "))
    if stop > limit * 0.6:
        return cut[: stop + 1]
    return cut.rsplit(" ", 1)[0].rstrip(",;:- ") + "…"


def safe_url(url: str) -> str:
    return url.replace(" ", "%20").replace(")", "%29").replace("(", "%28")


def time_ago(ts: datetime | None) -> str:
    if not ts:
        return ""
    secs = max(0, int((datetime.now(UTC) - ts).total_seconds()))
    if secs < 60:
        return "just now"
    if secs < 3600:
        return f"{secs // 60} min ago"
    if secs < 86400:
        return f"{secs // 3600} h ago"
    return f"{secs // 86400} d ago"


def pct_md(p: float) -> str:
    colour = "green" if p > 0 else "red" if p < 0 else "gray"
    return f":{colour}[{p:+.2f}%]"


# --------------------------------------------------------------- news data
def build_story(entry, source: str) -> dict | None:
    title = clean_text(entry.get("title", ""))
    link = entry.get("link", "")
    if not title or not link:
        return None
    shown_source = source
    if source == "Google News" and " - " in title:  # Google appends the publisher to titles
        title, publisher = title.rsplit(" - ", 1)
        shown_source = f"Google News ({publisher})"
    summary = clean_text(entry.get("summary") or entry.get("description") or "")
    if summary.lower().startswith(title.lower()[:40]) or SequenceMatcher(None, summary.lower(), title.lower()).ratio() > 0.8:
        summary = ""  # summary just repeats the headline
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    ts = datetime(*parsed[:6], tzinfo=UTC) if parsed else None
    blob = f"{title} {summary}"
    tags = [n for n, pats in PATTERNS.items() if any(p.search(blob) for p in pats)]
    topics = [t for t, p in TOPIC_PATTERNS.items() if p.search(blob)]
    if tags and "Companies" not in topics:
        topics.append("Companies")
    return {"title": title, "link": link, "source": shown_source, "feed": source, "summary": summary,
            "ts": ts, "tags": tags, "topics": topics or ["Markets"]}


def fetch_feed(item: tuple[str, str]):
    name, url = item
    try:
        resp = requests.get(url, headers=HEADERS, timeout=8)
        resp.raise_for_status()
        return name, feedparser.parse(resp.content).entries, None
    except Exception as exc:  # one bad feed must never break the page
        log.warning("Feed failed: %s (%s)", name, exc)
        return name, [], str(exc)


def dedupe(stories: list[dict]) -> list[dict]:
    norm = lambda t: re.sub(r"[^a-z0-9 ]", "", t.lower())
    kept, seen = [], set()
    for s in stories:
        key = norm(s["title"])
        if s["link"] in seen or key in seen:
            continue
        if any(SequenceMatcher(None, key, k["_key"]).ratio() > 0.88 for k in kept):
            continue
        s["_key"] = key
        seen.update((s["link"], key))
        kept.append(s)
    return kept


@st.cache_data(ttl=REFRESH_SECONDS, show_spinner=False)
def load_news():
    stories, failed = [], []
    with ThreadPoolExecutor(max_workers=6) as pool:
        for name, entries, err in pool.map(fetch_feed, SOURCES.items()):
            if err:
                failed.append(name)
            stories += [s for s in (build_story(e, name) for e in entries) if s]
    stories.sort(key=lambda s: s["ts"] or datetime.min.replace(tzinfo=UTC), reverse=True)
    return dedupe(stories)[:200], failed, datetime.now(IST)


# -------------------------------------------------------------- price data
@st.cache_data(ttl=REFRESH_SECONDS, show_spinner=False)
def load_prices(tickers: tuple[str, ...]) -> dict[str, tuple[float, float]]:
    """ticker -> (last close, % change vs previous close)."""
    try:
        df = yf.download(list(tickers), period="7d", interval="1d", group_by="ticker",
                         progress=False, auto_adjust=False, threads=True)
    except Exception as exc:
        log.warning("Price download failed: %s", exc)
        return {}
    out = {}
    for t in tickers:
        try:
            close = df[t]["Close"].dropna()
            if len(close) >= 2 and float(close.iloc[-2]) != 0:
                last, prev = float(close.iloc[-1]), float(close.iloc[-2])
                out[t] = (last, (last / prev - 1) * 100)
        except Exception:
            continue
    return out


def market_status() -> str:
    now = datetime.now(IST)
    is_open = now.weekday() < 5 and (9, 15) <= (now.hour, now.minute) <= (15, 30)
    return "Market open (prices may be delayed)" if is_open else "Market closed: showing the last session"


# -------------------------------------------------------------------- state
def init_state() -> None:
    defaults = {"topic": "All", "query": "", "today_only": False, "long_prev": True, "sources": list(SOURCES)}
    for key, val in defaults.items():
        st.session_state.setdefault(key, val)


def reset_filters() -> None:
    st.session_state.update(topic="All", query="", today_only=False, sources=list(SOURCES))


def apply_filters(stories: list[dict]) -> list[dict]:
    ss = st.session_state
    today = datetime.now(IST).date()
    q = ss["query"].strip().lower()
    out = []
    for s in stories:
        if s["feed"] not in ss["sources"]:
            continue
        if ss["topic"] != "All" and ss["topic"] not in s["topics"]:
            continue
        if ss["today_only"] and (not s["ts"] or s["ts"].astimezone(IST).date() != today):
            continue
        if q and q not in f"{s['title']} {s['summary']} {' '.join(s['tags'])}".lower():
            continue
        out.append(s)
    return out


# ---------------------------------------------------------------------- UI
def sidebar() -> None:
    with st.sidebar:
        st.header("Filters")
        st.radio("Topic", ["All", *TOPICS], key="topic")
        st.text_input("Search headlines", key="query", placeholder="e.g. RBI, Reliance, gold")
        st.checkbox("Today only", key="today_only")
        st.checkbox("Longer previews", key="long_prev", help="Show more of each story's summary.")
        st.multiselect("Sources", list(SOURCES), key="sources")
        left, right = st.columns(2)
        if left.button("🔄 Refresh now"):
            load_news.clear()
            load_prices.clear()
        right.button("Reset", on_click=reset_filters)
        if FEEDBACK_URL:
            st.link_button("Report a problem / feedback", FEEDBACK_URL)
        st.caption("For learning only. Not investment advice.")


def render_story(s: dict) -> None:
    with st.container(border=True):
        st.markdown(f"**[{md_safe(s['title'])}]({safe_url(s['link'])})**")
        st.caption(f"{s['source']} · {time_ago(s['ts'])}")
        if s["summary"]:
            st.markdown(md_safe(trim(s["summary"], 420 if st.session_state["long_prev"] else 200)))
        if s["tags"]:
            st.caption("Stocks mentioned: " + ", ".join(s["tags"]))


def metrics_row(prices: dict) -> None:
    for col, (label, tk) in zip(st.columns(len(INDICES)), INDICES.items()):
        val = prices.get(tk)
        if val:
            col.metric(label, f"{val[0]:,.2f}", f"{val[1]:+.2f}%",
                       help="Change vs previous close. Green = up, red = down.")
        else:
            col.metric(label, "—", help="Data unavailable right now.")


def news_tab(items: list[dict], total: int) -> None:
    if not items:
        st.info("No stories match your filters.")
        st.button("Reset filters", on_click=reset_filters, key="reset_empty")
        return
    st.caption(f"Showing {min(len(items), MAX_STORIES)} of {len(items)} matching stories ({total} loaded)")
    for s in items[:MAX_STORIES]:
        render_story(s)


def movers_tab(prices: dict) -> None:
    rows = [(n, *prices[tk]) for n, (tk, _) in COMPANIES.items() if tk in prices]
    if not rows:
        st.info("Price data is unavailable right now. Please try again in a minute.")
        return
    rows.sort(key=lambda r: r[2], reverse=True)
    gain, lose = st.columns(2)
    for col, title, subset in ((gain, "Top gainers", rows[:5]), (lose, "Top losers", rows[::-1][:5])):
        col.subheader(title)
        for name, price, pct in subset:
            col.metric(name, f"₹{price:,.2f}", f"{pct:+.2f}%")
    st.caption("Change vs previous close, among large NSE companies tracked here. "
               "Outside market hours this shows the last session.")


def focus_tab(stories: list[dict], prices: dict) -> None:
    by_stock: dict[str, list[dict]] = {}
    for s in stories:
        for tag in s["tags"]:
            by_stock.setdefault(tag, []).append(s)
    if not by_stock:
        st.info("No company mentions in the loaded stories yet.")
        return
    for name, group in sorted(by_stock.items(), key=lambda kv: len(kv[1]), reverse=True)[:8]:
        with st.container(border=True):
            st.markdown(f"**{md_safe(name)}**")
            st.caption(f"{len(group)} headline{'s' if len(group) != 1 else ''}")
            px = prices.get(COMPANIES[name][0])
            if px:
                st.markdown(f"₹{px[0]:,.2f} {pct_md(px[1])}")
            for s in group[:3]:
                st.markdown(f"- [{md_safe(s['title'])}]({safe_url(s['link'])})  \n"
                            f"  <small>{s['source']} · {time_ago(s['ts'])}</small>", unsafe_allow_html=True)


@st.fragment(run_every=f"{REFRESH_SECONDS}s")
def dashboard() -> None:
    """Only this block auto-refreshes, so scroll position, tab and filters are kept."""
    stories, failed, fetched_at = load_news()
    prices = load_prices(tuple(INDICES.values()) + tuple(t for t, _ in COMPANIES.values()))

    metrics_row(prices)
    items = apply_filters(stories)
    st.caption(f"Updated {fetched_at:%H:%M:%S} IST · {len(stories)} stories · {market_status()} · "
               f"auto-refresh every {REFRESH_SECONDS // 60} min")
    if failed:
        st.caption(f"⚠️ Some sources did not respond ({', '.join(failed)}). Showing the rest.")
    if not stories:
        st.error("Couldn't load any news right now. Please use Refresh now in a minute.")
        return
    if not prices:
        st.caption("⚠️ Price data is unavailable right now.")

    tab_news, tab_movers, tab_focus = st.tabs(["📰 News", "📈 Top gainers & losers", "🔥 Stocks in focus"])
    with tab_news:
        news_tab(items, len(stories))
    with tab_movers:
        movers_tab(prices)
    with tab_focus:
        focus_tab(stories, prices)


def main() -> None:
    init_state()
    st.markdown("<style>.block-container{padding-top:1.5rem}button{min-height:44px}</style>",
                unsafe_allow_html=True)
    sidebar()
    st.title("📈 Intellics")
    st.caption(f"Beta {VERSION} · Indian markets news · For learning only. Not investment advice. "
               "Tap » (top left) for filters.")
    dashboard()
    st.divider()
    st.caption("Headlines and summaries belong to their publishers; open the link to read the full story. "
               "Prices from Yahoo Finance and may be delayed.")
    if FEEDBACK_URL:
        st.link_button("Found a problem? Tell us", FEEDBACK_URL)


main()
