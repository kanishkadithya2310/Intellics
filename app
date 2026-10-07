"""Intellics Daily Finance Desk - live financial news + market tiles.
Run locally:  streamlit run app.py
"""
import html
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import feedparser
import pytz
import requests
import streamlit as st
import yfinance as yf

# ---------- SETTINGS ----------
REFRESH_SECONDS = 120   # news + prices refresh interval
MAX_ITEMS = 40
IST = pytz.timezone("Asia/Kolkata")
UA = {"User-Agent": "Mozilla/5.0 (compatible; IntellicsNewsDesk/1.0)"}

FEEDS = {
    "Economic Times": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "Moneycontrol": "https://www.moneycontrol.com/rss/marketreports.xml",
    "Mint": "https://www.livemint.com/rss/markets",
    "Business Standard": "https://www.business-standard.com/rss/markets-106.rss",
    "BusinessLine": "https://www.thehindubusinessline.com/markets/feeder/default.rss",
    "Google News": "https://news.google.com/rss/search?q=Sensex+OR+Nifty+OR+RBI+OR+rupee+OR+crude&hl=en-IN&gl=IN&ceid=IN:en",
}
TOPICS = {
    "All": [],
    "Markets": ["sensex", "nifty", "stock", "share", "market", "ipo", "index", "fii", "dii"],
    "Economy & RBI": ["rbi", "inflation", "gdp", "repo", "rate", "budget", "fiscal", "rupee", "economy", "tax", "bond"],
    "Companies": ["results", "profit", "earnings", "q1", "q2", "q3", "q4", "merger", "acquisition", "ceo", "order", "stake"],
    "Global": ["fed", "wall street", "china", "dollar", "europe", "global", "tariff", "us ", "asia"],
    "Commodities": ["gold", "silver", "crude", "brent", "oil", "commodity", "metal"],
}
TICKERS = {"Sensex": "^BSESN", "Nifty 50": "^NSEI", "USD/INR": "INR=X", "Brent crude": "BZ=F", "Gold": "GC=F"}

st.set_page_config(page_title="Intellics Daily Finance Desk", page_icon="📰", layout="wide")


# ---------- DATA ----------
def fetch_feed(name, url):
    try:
        r = requests.get(url, headers=UA, timeout=8)
        parsed = feedparser.parse(r.content)
        out = []
        for e in parsed.entries[:30]:
            t = e.get("published_parsed") or e.get("updated_parsed")
            when = datetime(*t[:6], tzinfo=pytz.utc).astimezone(IST) if t else None
            summary = re.sub(r"<[^>]+>", "", html.unescape(e.get("summary", ""))).strip()
            out.append({"title": html.unescape(e.get("title", "")).strip(), "link": e.get("link", "#"),
                        "source": name, "when": when, "summary": summary[:220]})
        return name, out, None
    except Exception as ex:
        return name, [], str(ex)[:60]


@st.cache_data(ttl=REFRESH_SECONDS, show_spinner=False)
def get_news():
    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(lambda kv: fetch_feed(*kv), FEEDS.items()))
    items, ok, failed = [], [], []
    for name, rows, err in results:
        (ok if rows else failed).append(name)
        items += rows
    seen, unique = set(), []
    for it in sorted(items, key=lambda x: x["when"] or datetime(2000, 1, 1, tzinfo=IST), reverse=True):
        key = re.sub(r"\W+", "", it["title"].lower())[:60]
        if key and key not in seen:
            seen.add(key)
            unique.append(it)
    return unique, ok, failed


@st.cache_data(ttl=60, show_spinner=False)
def get_tiles():
    def one(item):
        label, sym = item
        try:
            fi = yf.Ticker(sym).fast_info
            last = fi.get("last_price") or fi.get("lastPrice")
            prev = fi.get("previous_close") or fi.get("previousClose")
            return label, float(last), (float(last) / float(prev) - 1) * 100
        except Exception:
            return label, None, None
    with ThreadPoolExecutor(max_workers=5) as pool:
        return list(pool.map(one, TICKERS.items()))


def ago(when):
    if not when:
        return ""
    mins = int((datetime.now(IST) - when).total_seconds() // 60)
    if mins < 1:
        return "just now"
    if mins < 60:
        return f"{mins} min ago"
    if mins < 1440:
        return f"{mins // 60} h ago"
    return when.strftime("%d %b, %H:%M")


# ---------- UI ----------
st.title("📰 Intellics Daily Finance Desk")
st.caption("Live headlines from leading Indian business outlets, refreshed automatically. "
           "Each card links to the original article.")

with st.sidebar:
    st.header("Filters")
    topic = st.radio("Topic", list(TOPICS.keys()))
    query = st.text_input("Search headlines", placeholder="e.g. RBI, Reliance, gold")
    today_only = st.checkbox("Today only", value=False)
    source_pick = st.multiselect("Sources", list(FEEDS.keys()), default=list(FEEDS.keys()))
    if st.button("🔄 Refresh now"):
        st.cache_data.clear()
        st.rerun()
    st.caption("For learning only. Not investment advice.")


@st.fragment(run_every=REFRESH_SECONDS)
def desk(topic, query, today_only, source_pick):
    cols = st.columns(len(TICKERS))
    for col, (label, price, chg) in zip(cols, get_tiles()):
        if price is None:
            col.metric(label, "n/a")
        else:
            col.metric(label, f"{price:,.2f}", f"{chg:+.2f}%",
                       delta_color="inverse" if label in ("USD/INR", "Brent crude") else "normal")

    items, ok, failed = get_news()
    kws = TOPICS[topic]
    q = query.lower().strip()
    today = datetime.now(IST).date()
    shown = []
    for it in items:
        text = (it["title"] + " " + it["summary"]).lower()
        if it["source"] not in source_pick:
            continue
        if kws and not any(k in text for k in kws):
            continue
        if q and q not in text:
            continue
        if today_only and not (it["when"] and it["when"].date() == today):
            continue
        shown.append(it)

    st.caption(f"Updated {datetime.now(IST):%H:%M:%S} IST · {len(shown)} stories · "
               f"auto-refresh every {REFRESH_SECONDS // 60} min"
               + (f" · unavailable right now: {', '.join(failed)}" if failed else ""))
    if not shown:
        st.info("No stories match these filters yet. Try 'All' or turn off 'Today only'.")
    for it in shown[:MAX_ITEMS]:
        with st.container(border=True):
            st.markdown(f"**[{it['title']}]({it['link']})**")
            st.caption(f"{it['source']} · {ago(it['when'])}")
            if it["summary"]:
                st.write(it["summary"])


desk(topic, query, today_only, source_pick)
