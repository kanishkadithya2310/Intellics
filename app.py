"""Intellics v1.2 beta: Indian markets news, explained simply.

- Animated background (optional photo)
- Only well-known, reputable news sources (Economic Times, Moneycontrol, Mint, Business Standard,
  BusinessLine, Times of India, Hindustan Times, News18, Dalal Street Journal, HDFC Sky and
  Google News results limited to trusted publishers)
- Every article gets a 3-4 sentence plain-English summary (free Groq AI, with an
  automatic no-AI fallback so no article is ever left without one)
- Prices refresh every 30 seconds and show the time of the latest data point
- Top gainers & losers tab with a Groww/Zerodha-style company page: big price header, range buttons,
  line or candle chart with volume and moving averages, "why it moved" headlines on big days,
  today's and 52-week range bars, and a clean fundamentals table (P/E, debt to equity, ROE...)
- Upcoming dividends, splits and bonus issues
- 10 financial terms a day (600 unique terms in terms.py, no repeats for 60 days)
- Works on phones too: responsive cards, and the hero video always shows the whole picture
"""
from __future__ import annotations

import base64
import hashlib
import html
import json
import logging
import re
import textwrap
import threading
import time
import urllib.parse
from collections import Counter
from functools import lru_cache
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, wait
from datetime import date, datetime, timedelta, timezone
from difflib import SequenceMatcher
from zoneinfo import ZoneInfo

import feedparser
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
import yfinance as yf
from PIL import Image
from plotly.subplots import make_subplots

try:
    from terms import TERMS  # terms.py must sit next to app.py
except Exception:  # keep the app alive even if the file is missing
    TERMS = []

# ----------------------------------------------------------------- settings
VERSION = "1.2 beta"
NEWS_REFRESH = 120   # seconds between news refreshes
PRICE_REFRESH = 30   # seconds between price refreshes (as fast as the free source allows)
MAX_STORIES = 40
ORG_NAME = "Intellics Committee"
ORG_SUBTITLE = "The AI and Data Analytics Committee"
TAGLINE = "Think | Analyze | Evolve"
LOGO_PATH = Path(__file__).parent / "logo.png"  # upload logo.png next to this file
FEEDBACK_URL = ""          # paste your Google Form link to show a feedback button
BACKGROUND_IMAGE_URL = ""  # optional: a free photo URL (e.g. from Unsplash) for the page background
VIDEO_URL = "https://cdn.jsdelivr.net/gh/kanishkadithya2310/Intellics@main/hero.mp4"  # "" turns the video off
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.1-8b-instant"  # free-tier model; change if Groq renames it
IST, UTC = ZoneInfo("Asia/Kolkata"), timezone.utc
HEADERS = {"User-Agent": "Mozilla/5.0 (Intellics beta; learning project)"}


def _gnews(query: str) -> str:
    """Google News search feed (India edition). Used for sites that have no RSS feed of their own."""
    return ("https://news.google.com/rss/search?q=" + urllib.parse.quote_plus(query, safe=":")
            + "&hl=en-IN&gl=IN&ceid=IN:en")


# Only well-known, reputable publishers. Each source has one or more feed URLs; if the first
# one does not work, the next one is tried. To add or remove a source, edit this list.
SOURCES = {
    "Economic Times": ["https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms"],
    "Moneycontrol": ["https://www.moneycontrol.com/rss/MCtopnews.xml",
                     "https://www.moneycontrol.com/rss/latestnews.xml"],
    "Mint": ["https://www.livemint.com/rss/markets"],
    "Business Standard": ["https://www.business-standard.com/rss/markets-106.rss"],
    "BusinessLine": ["https://www.thehindubusinessline.com/markets/feeder/default.rss"],
    "Times of India": ["https://timesofindia.indiatimes.com/rssfeeds/1898055.cms"],
    "Hindustan Times": ["https://www.hindustantimes.com/feeds/rss/business/rssfeed.xml",
                        "https://www.hindustantimes.com/rss/business/rssfeed.xml"],
    "News18": ["https://www.news18.com/commonfeeds/v1/eng/rss/business.xml",
               "https://www.news18.com/rss/business.xml",
               "https://www.news18.com/rss/markets.xml"],
    # These two have no RSS feed of their own, so we read their latest articles through Google News.
    "Dalal Street Journal": [_gnews("site:dsij.in when:14d")],
    "HDFC Sky": [_gnews("site:hdfcsky.com when:7d")],
    "Google News": [_gnews("(Sensex OR Nifty OR RBI) when:1d")],
}
GOOGLE_SOURCES = {"Google News", "Dalal Street Journal", "HDFC Sky"}  # feeds whose titles end with " - Publisher"

# Google News mixes in every kind of website, so its stories are kept ONLY if the publisher is on this list.
TRUSTED_PUBLISHERS = {
    "times of india", "economic times", "mint", "livemint", "moneycontrol", "business standard",
    "hindu businessline", "businessline", "hindustan times", "news18", "cnbctv18", "cnbc-tv18",
    "dalal street investment journal", "dalal street journal", "dsij", "hdfc sky",
    "reuters", "financial express", "ndtv profit",
}


def trusted_publisher(name: str) -> bool:
    return re.sub(r"^the\s+", "", name.strip().lower()) in TRUSTED_PUBLISHERS


INDICES = {"Sensex": "^BSESN", "Nifty 50": "^NSEI", "Brent crude (USD/bbl)": "BZ=F", "Gold (USD/oz)": "GC=F"}

COMPANIES = {  # name -> (Yahoo ticker, alias regexes; short ALL-CAPS aliases match case-sensitively)
    "TCS": ("TCS.NS", ["TCS", "Tata Consultancy"]), "Infosys": ("INFY.NS", ["Infosys"]),
    "HCL Tech": ("HCLTECH.NS", ["HCL Tech", "HCLTech", "HCL Technologies"]), "Wipro": ("WIPRO.NS", ["Wipro"]),
    "Tech Mahindra": ("TECHM.NS", ["Tech Mahindra"]), "Reliance": ("RELIANCE.NS", ["Reliance(?! on\\b)"]),
    "HDFC Bank": ("HDFCBANK.NS", ["HDFC Bank"]), "ICICI Bank": ("ICICIBANK.NS", ["ICICI Bank"]),
    "SBI": ("SBIN.NS", ["SBI(?! Life| Cards)", "State Bank of India"]), "SBI Life": ("SBILIFE.NS", ["SBI Life"]),
    "Kotak Bank": ("KOTAKBANK.NS", ["Kotak Mahindra Bank", "Kotak Bank"]), "Axis Bank": ("AXISBANK.NS", ["Axis Bank"]),
    "ITC": ("ITC.NS", ["ITC(?! Hotels)"]), "L&T": ("LT.NS", ["Larsen", "L&T"]),
    "Tata Motors": ("TATAMOTORS.NS", ["Tata Motors"]), "Tata Steel": ("TATASTEEL.NS", ["Tata Steel"]),
    "Tata Power": ("TATAPOWER.NS", ["Tata Power"]), "Adani Ports": ("ADANIPORTS.NS", ["Adani Ports"]),
    "Adani Enterprises": ("ADANIENT.NS", ["Adani Enterprises"]), "Airtel": ("BHARTIARTL.NS", ["Airtel"]),
    "Maruti": ("MARUTI.NS", ["Maruti"]), "M&M": ("M&M.NS", ["M&M", "Mahindra & Mahindra"]),
    "Sun Pharma": ("SUNPHARMA.NS", ["Sun Pharma"]), "HUL": ("HINDUNILVR.NS", ["Hindustan Unilever", "HUL"]),
    "Asian Paints": ("ASIANPAINT.NS", ["Asian Paints"]), "Bajaj Finance": ("BAJFINANCE.NS", ["Bajaj Finance"]),
    "Titan": ("TITAN.NS", ["Titan"]), "JSW Steel": ("JSWSTEEL.NS", ["JSW Steel"]), "ONGC": ("ONGC.NS", ["ONGC"]),
    "NTPC": ("NTPC.NS", ["NTPC"]), "Power Grid": ("POWERGRID.NS", ["Power Grid"]),
    "Coal India": ("COALINDIA.NS", ["Coal India"]), "BEL": ("BEL.NS", ["BEL", "Bharat Electronics"]),
    "Polycab": ("POLYCAB.NS", ["Polycab"]),
}
TOPICS = {
    "Markets": ["sensex", "nifty", "stock market", "shares", "stocks", "bse", "nse", "ipo", "sebi", "fii", "fpi"],
    "Economy & RBI": ["rbi", "repo", "inflation", "gdp", "rate hike", "rate cut", "fiscal", "budget", "rupee", "economy", "gst"],
    "Companies": ["results", "earnings", "profit", "revenue", "acquisition", "merger", "ceo", "block deal", "order win"],
    "Global": ["fed", "treasury", "wall street", "china", "global", "dollar", "europe", "asia", "emerging market"],
    "Commodities": ["crude", "brent", "oil", "gold", "silver", "commodity", "opec", "natural gas", "copper"],
}
TOPIC_WHY = {
    "Markets": "This matters because market moves affect savings, investments and how confident investors feel.",
    "Economy & RBI": "This matters because decisions on interest rates and prices change the cost of loans and everyday spending.",
    "Companies": "This matters because a company's news can move its share price and affect its customers and employees.",
    "Global": "This matters because big world events often move Indian markets as well.",
    "Commodities": "This matters because oil and gold prices affect petrol costs, inflation and what people pay for things.",
}
GLOSSARY = [  # (name, regex, plain meaning)
    ("Block deal", r"block deals?", "a very large sale of shares between big investors, done in one go"),
    ("Repo rate", r"repo rate", "the interest rate at which the RBI lends money to banks; it affects loan rates"),
    ("Rate hike", r"rate hikes?", "when interest rates are raised, so loans become costlier"),
    ("Rate cut", r"rate cuts?", "when interest rates are lowered, so loans become cheaper"),
    ("Hawkish", r"hawkish", "leaning towards higher interest rates to keep prices under control"),
    ("52-week low", r"52-week lows?", "the lowest price a share has touched in the past year"),
    ("52-week high", r"52-week highs?", "the highest price a share has touched in the past year"),
    ("FII / FPI", r"FIIs?|FPIs?|(?i:foreign institutional|foreign portfolio)", "foreign investors who buy and sell Indian shares and bonds"),
    ("Inflation", r"inflation", "how fast everyday prices are rising"),
    ("GDP", r"GDP", "the total value of what a country produces; shows the size of its economy"),
    ("IPO", r"IPOs?", "when a company offers its shares to the public for the first time"),
    ("SEBI", r"SEBI", "India's market regulator, which makes rules to protect investors"),
    ("RBI", r"RBI", "the Reserve Bank of India, the country's central bank"),
    ("Sensex", r"Sensex", "an index of 30 big companies on the BSE that shows the market's overall mood"),
    ("Nifty", r"Nifty", "an index of 50 big companies on the NSE that shows the market's overall mood"),
    ("Brent crude", r"Brent", "the global benchmark price of crude oil"),
    ("Bond yields", r"treasury yields?|bond yields?", "the return investors earn on bonds; rising yields can pull money out of shares"),
    ("Market cap", r"market cap(?:italisation|italization)?", "a company's total value on the stock market"),
    ("Dividend", r"dividends?", "a share of profit that a company pays to its shareholders"),
    ("Insolvency", r"insolvency", "when a company cannot repay its debts"),
    ("Acquisition", r"acquisitions?|acquires?", "when one company buys another"),
    ("Merger", r"mergers?", "when two companies join to become one"),
    ("EBITDA", r"EBITDA", "profit from a company's core business before interest, tax and similar costs"),
    ("Margins", r"margins?", "how much profit a company keeps from each rupee of sales"),
    ("SMA", r"SMAs?", "a simple moving average: an average price over a period that traders use to spot trends"),
    ("CASA", r"CASA", "money a bank holds in low-cost savings and current accounts"),
    ("NPA", r"NPAs?", "a loan the borrower has stopped repaying"),
    ("Fed", r"Fed", "the US central bank; its interest rate decisions affect markets worldwide"),
    ("Tariff", r"tariffs?", "a tax on goods brought in from other countries"),
    ("GST", r"GST", "Goods and Services Tax, the tax added to most things we buy"),
    ("Quarter (Q1-Q4)", r"Q[1-4]", "a three-month part of a company's financial year (Q1 is April to June)"),
    ("Bullish / Bearish", r"bullish|bearish", "expecting prices to rise (bullish) or fall (bearish)"),
    ("Intraday", r"intraday", "within a single trading day"),
    ("Circuit limit", r"upper circuit|lower circuit", "the daily limit beyond which a share's price is not allowed to move"),
]
SYSTEM_PROMPT = (
    "You explain Indian business news to students from any background (MBA, BBA, arts). "
    "For each story write a summary of 3 to 4 short sentences in very simple English, as if explaining to a friend. "
    "Avoid jargon; if a term is unavoidable, explain it in plain words in brackets. "
    "Use ONLY the headline and snippet given; never invent numbers, names or causes. "
    "If little detail is given, say what the headline tells us and explain what its terms mean. "
    'Reply with JSON only, like {"1": "summary", "2": "summary"}, using the story numbers as keys.'
)

PLOT_KW = {} if hasattr(st, "iframe") else {"use_container_width": True}  # new vs old Streamlit
log = logging.getLogger("intellics")
logging.basicConfig(level=logging.INFO)
try:
    PAGE_ICON = Image.open(LOGO_PATH)
except Exception:
    PAGE_ICON = "📈"
st.set_page_config(page_title="Intellics Committee", page_icon=PAGE_ICON, layout="wide", initial_sidebar_state="collapsed")


def _compile(alias: str) -> re.Pattern:
    base = alias.split("(")[0]
    return re.compile(rf"(?<![A-Za-z0-9]){alias}(?![A-Za-z0-9])", 0 if base.isupper() and len(base) <= 5 else re.I)


PATTERNS = {n: [_compile(a) for a in als] for n, (_, als) in COMPANIES.items()}
TOPIC_PATTERNS = {t: re.compile(r"\b(" + "|".join(map(re.escape, kw)) + r")\b", re.I) for t, kw in TOPICS.items()}
CASE_SENSITIVE = {"FII / FPI", "GDP", "IPO", "SEBI", "RBI", "EBITDA", "SMA", "CASA", "NPA", "Fed", "GST", "Quarter (Q1-Q4)"}
GLOSS_PATTERNS = [(n, re.compile(rf"(?<![A-Za-z0-9])(?:{p})(?![A-Za-z0-9])", 0 if n in CASE_SENSITIVE else re.I), m)
                  for n, p, m in GLOSSARY]


# ------------------------------------------------------------ text helpers
def clean_text(raw: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", raw or ""))).strip()


def md_safe(text: str) -> str:
    return re.sub(r"([\\`*_\[\]$~#<>|])", r"\\\1", text)


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


def glossary_hits(blob: str) -> list[tuple[str, str]]:
    return [(n, m) for n, p, m in GLOSS_PATTERNS if p.search(blob)]


# --------------------------------------------------------------- news data
def build_story(entry, source: str) -> dict | None:
    title, link = clean_text(entry.get("title", "")), entry.get("link", "")
    if not title or not link:
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


def fetch_feed(item):
    """item = (source name, list of feed URLs). Tries each URL in order until one gives stories."""
    name, urls = item
    err = "no stories found"
    for url in urls:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=8)
            resp.raise_for_status()
            entries = feedparser.parse(resp.content).entries
            if entries:
                return name, entries, None
        except Exception as exc:
            err = str(exc)
            log.warning("Feed failed: %s %s (%s)", name, url, exc)
    return name, [], err


def dedupe(stories: list[dict]) -> list[dict]:
    norm = lambda t: re.sub(r"[^a-z0-9 ]", "", t.lower())
    kept, seen = [], set()
    for s in stories:
        key = norm(s["title"])
        if s["link"] in seen or key in seen or any(SequenceMatcher(None, key, k["_key"]).ratio() > 0.88 for k in kept):
            continue
        s["_key"] = key
        seen.update((s["link"], key))
        kept.append(s)
    return kept


@st.cache_data(ttl=NEWS_REFRESH, show_spinner=False)
def load_news():
    stories, failed = [], []
    with ThreadPoolExecutor(max_workers=8) as pool:
        for name, entries, err in pool.map(fetch_feed, SOURCES.items()):
            failed += [name] if err else []
            stories += [s for s in (build_story(e, name) for e in entries) if s]
    stories.sort(key=lambda s: s["ts"] or datetime.min.replace(tzinfo=UTC), reverse=True)
    return dedupe(stories)[:200], failed, datetime.now(IST)


# --------------------------------------------------- simple-language summaries
@st.cache_resource
def _store():
    return {"data": {}, "pending": set(), "lock": threading.Lock(), "pool": ThreadPoolExecutor(max_workers=2)}


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
            log.warning("AI summary batch failed: %s", exc)
            break
    store = _store()
    with store["lock"]:
        for i, s in enumerate(batch, 1):
            text = str(result.get(str(i), "")).strip()
            if len(text) >= 100:
                store["data"][s["id"]] = {"t": text, "m": "ai", "at": time.time()}
            store["pending"].discard(s["id"])


def get_summaries(stories: list[dict]) -> dict[str, dict]:
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
        wait(futures, timeout=25)  # slow batches keep running and show up on the next refresh
    return {s["id"]: store["data"][s["id"]] for s in stories}


# -------------------------------------------------------------- price data
def _fast_info(ticker: str):
    fi = yf.Ticker(ticker).fast_info
    last, prev = float(fi["last_price"]), float(fi["previous_close"])
    return ticker, (last, (last / prev - 1) * 100)


@st.cache_data(ttl=PRICE_REFRESH, show_spinner=False)
def load_prices(tickers: tuple[str, ...]) -> dict[str, tuple[float, float]]:
    out: dict = {}
    try:
        df = yf.download(list(tickers), period="7d", interval="1d", group_by="ticker",
                         progress=False, auto_adjust=False, threads=True)
        for t in tickers:
            try:
                close = df[t]["Close"].dropna()
                if len(close) >= 2 and float(close.iloc[-2]) != 0:
                    out[t] = (float(close.iloc[-1]), (float(close.iloc[-1]) / float(close.iloc[-2]) - 1) * 100)
            except Exception:
                continue
    except Exception as exc:
        log.warning("Batch price download failed: %s", exc)
    missing = [t for t in tickers if t not in out]
    if len(missing) > len(tickers) // 2:  # second route so the gainers/losers page is never empty
        with ThreadPoolExecutor(max_workers=8) as pool:
            for res in pool.map(lambda t: _safe(_fast_info, t), missing):
                if res:
                    out[res[0]] = res[1]
    return out


def _safe(fn, arg):
    try:
        return fn(arg)
    except Exception:
        return None


@st.cache_data(ttl=600, show_spinner=False)
def load_history(ticker: str):
    try:
        return yf.Ticker(ticker).history(period="1mo")["Close"].dropna()
    except Exception:
        return None


@st.cache_data(ttl=PRICE_REFRESH, show_spinner=False)
def load_data_time():
    """Time of the newest 1-minute price point Yahoo has for the Nifty (shows how fresh the data really is)."""
    try:
        df = yf.download("^NSEI", period="1d", interval="1m", progress=False, auto_adjust=False)
        if len(df):
            ts = df.index[-1]
            ts = ts.tz_localize("UTC") if ts.tzinfo is None else ts
            return ts.tz_convert(IST).to_pydatetime()
    except Exception as exc:
        log.warning("Data-time lookup failed: %s", exc)
    return None


def all_tickers() -> tuple[str, ...]:
    return tuple(INDICES.values()) + tuple(t for t, _ in COMPANIES.values())


def mover_rows(prices: dict) -> list[tuple[str, str, float, float]]:
    rows = [(n, tk, *prices[tk]) for n, (tk, _) in COMPANIES.items() if tk in prices]
    return sorted(rows, key=lambda r: r[3], reverse=True)


def market_status() -> str:
    now = datetime.now(IST)
    open_ = now.weekday() < 5 and (9, 15) <= (now.hour, now.minute) <= (15, 30)
    return "Market open (prices may be delayed)" if open_ else "Market closed: showing the last session"


# ------------------------------------------------------------ look and feel
def inject_css() -> None:
    photo = (f"linear-gradient(rgba(8,12,28,.82),rgba(8,12,28,.9)),url('{BACKGROUND_IMAGE_URL}') center/cover fixed"
             if BACKGROUND_IMAGE_URL else "")
    st.markdown(f"""<style>
.stApp{{background:{photo or 'radial-gradient(1100px 600px at 8% -10%,#1d3157 0%,transparent 60%),radial-gradient(900px 520px at 100% 0%,#3b1d5e 0%,transparent 55%),#0a0f1f fixed'};}}
.stApp::before{{content:"";position:fixed;inset:0;pointer-events:none;z-index:0;
 background-image:linear-gradient(rgba(255,255,255,.03) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.03) 1px,transparent 1px);
 background-size:42px 42px;animation:drift 40s linear infinite}}
@keyframes drift{{to{{background-position:42px 42px}}}}
.block-container{{padding-top:4.5rem;max-width:1100px;position:relative;z-index:1}}
div[class*="st-key-card_"]{{background:rgba(255,255,255,.05);backdrop-filter:blur(10px);border:1px solid rgba(255,255,255,.1);
 border-radius:18px;padding:.4rem .6rem;transition:transform .2s,border-color .2s}}
div[class*="st-key-card_"]:hover{{transform:translateY(-3px);border-color:rgba(120,160,255,.6)}}
.hero-title{{font-size:2rem;font-weight:800;letter-spacing:.12em;line-height:1.15;margin:0}}
.brand{{display:flex;align-items:center;gap:16px;margin-bottom:.3rem}}
.hero-sub{{opacity:.8;margin-bottom:.6rem}}
.mood{{height:12px;border-radius:99px;overflow:hidden;background:#ef4444;margin:.3rem 0 .2rem}}
.mood>div{{height:100%;background:#22c55e;transition:width .6s}}
button{{min-height:44px;border-radius:12px!important}}
.stat-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:.4rem 0 .6rem}}
.stat{{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.1);border-radius:14px;padding:10px 12px;backdrop-filter:blur(8px)}}
.stat .l{{font-size:.74rem;opacity:.72;letter-spacing:.02em}}
.stat .v{{font-size:1.3rem;font-weight:700;line-height:1.3}}
.stat .d{{font-size:.8rem;font-weight:600}}
.stat .d.up{{color:#4ade80}}.stat .d.dn{{color:#f87171}}
.px-head{{margin:.2rem 0 .6rem}}
.px-name{{font-size:1.25rem;font-weight:700}}
.px-sec{{font-size:.8rem;opacity:.7;margin-bottom:.2rem}}
.px-row{{display:flex;align-items:baseline;flex-wrap:wrap;gap:4px 14px}}
.px-price{{font-size:2rem;font-weight:800;line-height:1.2}}
.px-chg{{font-size:1rem;font-weight:700}}
.px-chg.up{{color:#4ade80}}.px-chg.dn{{color:#f87171}}
.px-sub{{font-size:.76rem;opacity:.65}}
.ftab{{display:grid;grid-template-columns:1fr 1fr;column-gap:32px;margin:.2rem 0 .8rem}}
.fr{{display:flex;justify-content:space-between;gap:12px;padding:10px 2px;border-bottom:1px solid rgba(255,255,255,.09);font-size:.92rem}}
.fr .k{{opacity:.72}}.fr .v{{font-weight:600;text-align:right}}
.rb{{margin:.4rem 0 1rem}}
.rb .ends{{display:flex;justify-content:space-between;font-size:.8rem;opacity:.9;line-height:1.35}}
.rb .track{{position:relative;height:6px;border-radius:99px;background:linear-gradient(90deg,#ef4444,#f59e0b,#22c55e);margin:8px 0 2px}}
.rb .dot{{position:absolute;top:-5px;width:16px;height:16px;border-radius:50%;background:#fff;border:3px solid #0a0f1f;transform:translateX(-50%);box-sizing:border-box}}
@media (max-width:640px){{.hero-title{{font-size:1.25rem;letter-spacing:.06em}}.brand img{{height:56px!important;width:56px!important}}
.block-container{{padding-left:.9rem;padding-right:.9rem}}.stat-grid{{grid-template-columns:repeat(2,1fr)}}.stat .v{{font-size:1.1rem}}
.ftab{{grid-template-columns:1fr}}.px-price{{font-size:1.6rem}}}}
@media (prefers-reduced-motion:reduce){{.stApp::before{{animation:none}}div[class*="st-key-card_"]{{transition:none}}}}
</style>""", unsafe_allow_html=True)


def video_background() -> None:
    """Full-screen looping hero video. Set VIDEO_URL = "" to switch it off.
    Laptop (wide screen): the video fills the screen.
    Phone (tall screen): the whole video is shown at the top, so the bull and bear are never cropped."""
    if not VIDEO_URL:
        return
    st.markdown(f"""<style>
html,body{{background:#0a0f1f}}
.stApp,[data-testid="stAppViewContainer"],[data-testid="stHeader"]{{background:transparent!important}}
.stApp::before{{display:none}}
.hero-video{{position:fixed;top:0;left:0;width:100vw;height:100vh;object-fit:cover;z-index:-1;background:#0a0f1f}}
.hero-overlay{{position:fixed;inset:0;background:rgba(10,15,31,.55);z-index:-1}}
@media (max-aspect-ratio:1/1){{
.hero-video{{object-fit:contain;object-position:center top}}
.hero-overlay{{background:rgba(10,15,31,.2)}}
.block-container{{padding-top:calc(56.25vw + 1rem)!important}}
}}
</style>
<video class="hero-video" autoplay loop muted playsinline>
<source src="{VIDEO_URL}" type="video/mp4"></video>
<div class="hero-overlay"></div>""", unsafe_allow_html=True)


@lru_cache(maxsize=1)
def logo_html() -> str:
    try:
        b64 = base64.b64encode(LOGO_PATH.read_bytes()).decode()
        return f'<img src="data:image/png;base64,{b64}" alt="{ORG_NAME} logo" style="height:78px;width:78px;flex:none;border-radius:16px">'
    except OSError:
        return '<div style="font-size:3rem;flex:none">📈</div>'  # logo.png missing: fall back to an emoji


def header() -> None:
    st.markdown(f'<div class="brand">{logo_html()}<div><div class="hero-title">{ORG_NAME}</div>'
                f'<div class="hero-sub" style="margin:.15rem 0 0">{ORG_SUBTITLE} · {TAGLINE}</div></div></div>'
                '<div class="hero-sub">Indian market news and prices, in plain English.</div>', unsafe_allow_html=True)


def mood_bar(rows: list) -> None:
    if not rows:
        return
    up = sum(1 for r in rows if r[3] > 0)
    st.markdown(f'<div class="mood"><div style="width:{up / len(rows) * 100:.0f}%"></div></div>', unsafe_allow_html=True)
    st.caption(f"Market mood: 🟢 {up} up · 🔴 {len(rows) - up} down among {len(rows)} large companies tracked")


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
    st.pills("Topic", ["All", *TOPICS], selection_mode="single", default="All", key="topic", label_visibility="collapsed")
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
def render_story(s: dict, summ: dict) -> None:
    with st.container(border=True, key=f"card_{s['id']}"):
        st.markdown(f"**[{md_safe(s['title'])}]({safe_url(s['link'])})**")
        st.markdown(" ".join(f":blue-badge[{t}]" for t in s["topics"][:2]) + f"  \n<small>{md_safe(s['source'])} · {time_ago(s['ts'])}</small>",
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
    st.caption(f"Showing {len(items)} stories ({total} loaded)")
    with st.spinner("Loading summaries…"):
        summaries = get_summaries(items)
    for s in items:
        render_story(s, summaries[s["id"]])


def movers_tab(rows: list, stories: list[dict]) -> None:
    if not rows:
        st.info("Price data didn't load this time. Tap the button to try again.")
        st.button("🔄 Try again", on_click=refresh_all, key="retry_prices")
        return
    shown = rows[:6] + rows[-6:]
    vals = [r[3] for r in shown]
    span = max(abs(v) for v in vals) or 1
    fig = go.Figure(go.Bar(x=vals[::-1], y=[r[0] for r in shown][::-1], orientation="h", cliponaxis=False,
                           marker_color=["#22c55e" if v >= 0 else "#ef4444" for v in vals][::-1],
                           text=[f"{v:+.2f}%" for v in vals][::-1], textposition="outside",
                           hovertemplate="%{y}: %{x:+.2f}%<extra></extra>"))
    fig.update_layout(height=440, margin=dict(l=0, r=10, t=10, b=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font_color="#e5e7eb", xaxis_title="% change vs previous close", dragmode=False)
    # leave room on both sides so the % labels at the end of long bars are never cut off
    fig.update_xaxes(range=[min(0, min(vals)) - span * 0.3, max(0, max(vals)) + span * 0.3], zeroline=True,
                     zerolinecolor="rgba(255,255,255,.35)")
    fig.update_yaxes(automargin=True)
    st.plotly_chart(fig, **PLOT_KW, config={"displayModeBar": False})
    g, l = st.columns(2)
    g.subheader("🟢 Top gainers")
    l.subheader("🔴 Top losers")
    for col, subset in ((g, rows[:5]), (l, rows[::-1][:5])):
        for name, _, price, pct in subset:
            col.metric(name, f"₹{price:,.2f}", f"{pct:+.2f}%")
    st.caption("Change vs previous close, among large NSE companies tracked here. Outside market hours this shows the last session.")

    company_explorer(rows, stories)


# ------------------------------------------------------- company deep-dive
RANGES = {"1D": ("1d", "5m"), "1W": ("5d", "15m"), "1M": ("1mo", "1d"), "3M": ("3mo", "1d"),
          "6M": ("6mo", "1d"), "1Y": ("1y", "1d"), "5Y": ("5y", "1wk")}


@st.cache_data(ttl=300, show_spinner=False)
def load_ohlc(ticker: str, period: str, interval: str):
    try:
        df = yf.Ticker(ticker).history(period=period, interval=interval)[["Open", "High", "Low", "Close", "Volume"]]
        df = df.dropna(subset=["Open", "High", "Low", "Close"])
        df["Volume"] = df["Volume"].fillna(0)
        return df if len(df) > 1 else None
    except Exception as exc:
        log.warning("History failed for %s: %s", ticker, exc)
        return None


def big_moves(df, weekly: bool) -> list[tuple]:
    """Up to 3 of the biggest single-day (or single-week) moves, only if they are large enough to matter."""
    ret = df["Close"].pct_change() * 100
    limit = 6.0 if weekly else 3.0
    out = []
    for pos in ret.abs().reset_index(drop=True).nlargest(3).index:
        if abs(ret.iloc[pos]) >= limit:
            out.append((df.index[pos], float(df["Close"].iloc[pos]), float(ret.iloc[pos])))
    return sorted(out, key=lambda m: m[0])


@st.cache_data(ttl=6 * 3600, show_spinner=False)
def move_headline(name: str, day: str):
    """Top news result about a company around a given date, from a trusted publisher only (Google News search by date)."""
    d = datetime.strptime(day, "%Y-%m-%d").date()
    query = f'"{name}" (shares OR stock OR results) after:{d - timedelta(days=1)} before:{d + timedelta(days=2)}'
    url = "https://news.google.com/rss/search?" + urllib.parse.urlencode(
        {"q": query, "hl": "en-IN", "gl": "IN", "ceid": "IN:en"})
    try:
        resp = requests.get(url, headers=HEADERS, timeout=8)
        resp.raise_for_status()
        for entry in feedparser.parse(resp.content).entries[:12]:
            title, publisher = clean_text(entry.get("title", "")), ""
            if " - " in title:
                title, publisher = title.rsplit(" - ", 1)
            if title and entry.get("link") and trusted_publisher(publisher):
                return {"title": title, "publisher": publisher.strip(), "link": entry["link"]}
    except Exception as exc:
        log.warning("Move headline failed (%s, %s): %s", name, day, exc)
    return None


@st.cache_data(ttl=3600, show_spinner=False)
def load_fundamentals(ticker: str) -> dict:
    keys = ("trailingPE", "forwardPE", "priceToBook", "debtToEquity", "returnOnEquity", "profitMargins", "marketCap",
            "fiftyTwoWeekHigh", "fiftyTwoWeekLow", "dividendRate", "trailingEps", "bookValue", "sector", "industry")
    out: dict = {}
    try:
        tk = yf.Ticker(ticker)
        info = tk.info or {}
        out = {k: info[k] for k in keys if info.get(k) is not None}
        for key, fast_key in (("marketCap", "market_cap"), ("fiftyTwoWeekHigh", "year_high"), ("fiftyTwoWeekLow", "year_low")):
            if key not in out:  # backup route if the full info call is missing a number
                try:
                    out[key] = float(tk.fast_info[fast_key])
                except Exception:
                    pass
    except Exception as exc:
        log.warning("Fundamentals failed for %s: %s", ticker, exc)
    return out


@st.cache_data(ttl=PRICE_REFRESH, show_spinner=False)
def load_day_stats(ticker: str) -> dict:
    """Today's open, high, low, previous close and volume (refreshed often, unlike the yearly numbers)."""
    out: dict = {}
    try:
        fi = yf.Ticker(ticker).fast_info
    except Exception:
        return out
    for key, fast_key in (("dayHigh", "day_high"), ("dayLow", "day_low"), ("open", "open"),
                          ("prevClose", "previous_close"), ("volume", "last_volume")):
        try:
            v = float(fi[fast_key])
            if v == v:  # skip NaN
                out[key] = v
        except Exception:
            pass
    return out


def _num(v, suffix: str = "", digits: int = 1) -> str:
    return "—" if v is None else f"{v:,.{digits}f}{suffix}"


def _rs(v, digits: int = 2) -> str:
    return "—" if v is None else f"₹{v:,.{digits}f}"


def _crore(v) -> str:
    if not v:
        return "—"
    cr = v / 1e7
    return f"₹{cr / 1e5:,.2f} lakh cr" if cr >= 1e5 else f"₹{cr:,.0f} cr"


def _volume(v) -> str:
    if not v:
        return "—"
    return f"{v / 1e7:,.2f} cr" if v >= 1e7 else f"{v / 1e5:,.2f} lakh" if v >= 1e5 else f"{v:,.0f}"


def info_table(items: list[tuple]) -> None:
    """Clean two-column table like Groww/Zerodha: label on the left, value on the right. items = (label, value, tooltip)."""
    cells = "".join(f'<div class="fr" title="{html.escape(tip, quote=True)}"><span class="k">{html.escape(k)}</span>'
                    f'<span class="v">{html.escape(v)}</span></div>' for k, v, tip in items)
    st.markdown(f'<div class="ftab">{cells}</div>', unsafe_allow_html=True)


def range_bar(lo_label: str, hi_label: str, lo, hi, price) -> str:
    """A low-to-high bar with a dot showing where the price is now."""
    if not (lo and hi and hi > lo and price):
        return ""
    pos = min(max((price - lo) / (hi - lo), 0.0), 1.0) * 100
    return (f'<div class="rb"><div class="ends"><span>{html.escape(lo_label)}<br><b>₹{lo:,.2f}</b></span>'
            f'<span style="text-align:right">{html.escape(hi_label)}<br><b>₹{hi:,.2f}</b></span></div>'
            f'<div class="track"><i class="dot" style="left:{pos:.1f}%"></i></div></div>')


def analysis_card(price: float, f: dict, day: dict) -> None:
    if not f and not day:
        st.info("Company numbers aren't available right now. Please try again in a few minutes.")
        return
    st.markdown("**📈 Performance**")
    bars = (range_bar("Today's low", "Today's high", day.get("dayLow"), day.get("dayHigh"), price)
            + range_bar("52-week low", "52-week high", f.get("fiftyTwoWeekLow"), f.get("fiftyTwoWeekHigh"), price))
    if bars:
        st.markdown(bars, unsafe_allow_html=True)
    info_table([
        ("Open", _rs(day.get("open")), "The price at which the share started trading today."),
        ("Prev. close", _rs(day.get("prevClose")), "The price at which the share closed on the previous trading day."),
        ("Volume", _volume(day.get("volume")), "How many shares have changed hands today."),
        ("Market cap", _crore(f.get("marketCap")), "The total value of the company on the stock market."),
    ])

    de, roe, pm = f.get("debtToEquity"), f.get("returnOnEquity"), f.get("profitMargins")
    de = de / 100 if de is not None else None      # Yahoo gives debt/equity as a percentage
    roe = roe * 100 if roe is not None else None   # Yahoo gives ROE and margin as fractions (0.15 = 15%)
    pm = pm * 100 if pm is not None else None
    dy = f["dividendRate"] / price * 100 if f.get("dividendRate") and price else None
    st.markdown("**📋 Fundamentals**")
    info_table([
        ("P/E ratio", _num(f.get("trailingPE"), "x"),
         "Share price divided by yearly profit per share. A P/E of 20 means investors pay Rs 20 for every Rs 1 of yearly profit. Compare it with similar companies."),
        ("P/B ratio", _num(f.get("priceToBook"), "x", 2),
         "Share price compared with the company's book value (assets minus debts) per share."),
        ("EPS (yearly)", _rs(f.get("trailingEps")), "Profit earned per share over the last year."),
        ("Book value", _rs(f.get("bookValue")), "The company's net worth (assets minus debts) per share."),
        ("Debt to equity", _num(de, "x", 2),
         "How much the company has borrowed for every Rs 1 of its own money. Lower usually means less risk. Not meaningful for banks."),
        ("Return on equity", _num(roe, "%"), "Profit earned on shareholders' money. Higher usually means the company uses money well."),
        ("Profit margin", _num(pm, "%"), "The share of sales the company keeps as profit."),
        ("Dividend yield", _num(dy, "%", 2), "Yearly dividend as a percentage of the share price."),
    ])
    with st.expander("How to read these numbers"):
        st.markdown("- **P/E**: lower can mean cheaper, higher can mean investors expect growth. Compare within the same industry.\n"
                    "- **Debt to equity**: above 1 means more borrowed money than own money (normal for banks and finance firms).\n"
                    "- **Return on equity**: 15% or more is often seen as good.\n"
                    "- **Range bars**: the closer the dot is to the right, the closer the price is to its high.")
    st.caption("Numbers come from Yahoo Finance and can be missing or out of date. They are for learning, not advice to buy or sell.")


def _breaks(df, interval: str, intraday: bool) -> list[dict]:
    """Hide weekends, non-trading hours and market holidays so the chart has no empty gaps."""
    breaks = [dict(bounds=["sat", "mon"])]
    if intraday:
        breaks.append(dict(bounds=[15.5, 9.25], pattern="hour"))
    elif interval == "1d":
        have = set(df.index.date)
        missing = [d.strftime("%Y-%m-%d") for d in pd.bdate_range(df.index[0].date(), df.index[-1].date()) if d.date() not in have]
        if missing:
            breaks.append(dict(values=missing))
    return breaks


def build_chart(df, name: str, kind: str, intraday: bool, interval: str, moves: list, heads: dict,
                ref: float, show_vol: bool, smas: set):
    up = float(df["Close"].iloc[-1]) >= ref
    color, fill = ("#22c55e", "rgba(34,197,94,.14)") if up else ("#ef4444", "rgba(239,68,68,.14)")
    fig = make_subplots(rows=2 if show_vol else 1, cols=1, shared_xaxes=True, vertical_spacing=0.03,
                        row_heights=[0.78, 0.22] if show_vol else [1.0])
    if kind == "Candles":
        fig.add_trace(go.Candlestick(x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
                                     increasing_line_color="#22c55e", decreasing_line_color="#ef4444",
                                     name=name, showlegend=False), row=1, col=1)
        hi_s, lo_s = df["High"], df["Low"]
    else:
        fig.add_trace(go.Scatter(x=df.index, y=df["Close"], mode="lines", name="Price", showlegend=False,
                                 line=dict(color=color, width=2.2), fill="tozeroy", fillcolor=fill,
                                 hovertemplate="Price ₹%{y:,.2f}<extra></extra>"), row=1, col=1)
        fig.add_hline(y=ref, line_dash="dot", line_color="rgba(148,163,184,.55)", line_width=1, row=1, col=1)
        hi_s, lo_s = df["Close"], df["Close"]
    for n, col in ((20, "#f59e0b"), (50, "#60a5fa")):
        if n in smas and len(df) > n:
            fig.add_trace(go.Scatter(x=df.index, y=df["Close"].rolling(n).mean(), mode="lines", name=f"SMA {n}",
                                     line=dict(color=col, width=1.4), hovertemplate=f"SMA {n} ₹%{{y:,.2f}}<extra></extra>"),
                          row=1, col=1)
    if moves:
        text = []
        for ts, _, pct in moves:
            head = heads.get(ts)
            line = f"{ts:%d %b}: {pct:+.1f}%"
            if head:
                line += "<br>" + textwrap.fill(head["title"], 42).replace("\n", "<br>")
            text.append(line)
        fig.add_trace(go.Scatter(x=[m[0] for m in moves], y=[m[1] for m in moves], mode="markers", showlegend=False, name="Big move",
                                 marker=dict(size=13, symbol="diamond", line=dict(width=1.5, color="white"),
                                             color=["#22c55e" if m[2] > 0 else "#ef4444" for m in moves]),
                                 text=text, hovertemplate="%{text}<extra></extra>"), row=1, col=1)
    if show_vol:
        vcol = ["rgba(34,197,94,.55)" if c >= o else "rgba(239,68,68,.55)" for o, c in zip(df["Open"], df["Close"])]
        fig.add_trace(go.Bar(x=df.index, y=df["Volume"], marker_color=vcol, name="Volume", showlegend=False,
                             hovertemplate="Volume %{y:,.0f}<extra></extra>"), row=2, col=1)
        fig.update_yaxes(showgrid=False, side="right", tickformat=".2s", row=2, col=1)
    hi, lo = float(hi_s.max()), float(lo_s.min())
    for ts, val, ay in ((hi_s.idxmax(), hi, -24), (lo_s.idxmin(), lo, 24)):
        fig.add_annotation(x=ts, y=val, text=f"₹{val:,.2f}", showarrow=True, arrowhead=0, ax=0, ay=ay,
                           arrowcolor="rgba(148,163,184,.8)", font=dict(size=11, color="#e5e7eb"), row=1, col=1)
    pad = (hi - lo) * 0.09 or 1
    fig.update_xaxes(rangebreaks=_breaks(df, interval, intraday), rangeslider_visible=False, showgrid=False,
                     showspikes=True, spikemode="across", spikesnap="cursor", spikethickness=1, spikedash="dot",
                     spikecolor="#94a3b8", hoverformat="%d %b %Y, %I:%M %p" if intraday else "%d %b %Y")
    fig.update_yaxes(range=[lo - pad, hi + pad], side="right", showgrid=True, gridcolor="rgba(255,255,255,.07)",
                     tickprefix="₹", zeroline=False, row=1, col=1)
    fig.update_layout(height=440 if show_vol else 360, margin=dict(l=0, r=0, t=8, b=0), paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", font_color="#e5e7eb", dragmode=False, hovermode="x unified",
                      hoverlabel=dict(bgcolor="#111827", font_color="#f9fafb"), showlegend=bool(smas),
                      legend=dict(orientation="h", y=1.04, x=0))
    return fig


def company_explorer(rows: list, stories: list[dict]) -> None:
    st.subheader("🔍 Explore a company")
    pick = st.selectbox("Search or pick a company", [r[0] for r in rows], key="explore")
    row = next(r for r in rows if r[0] == pick)
    ticker, price, day_pct = row[1], row[2], row[3]
    with st.spinner("Loading company numbers…"):
        fund, day = load_fundamentals(ticker), load_day_stats(ticker)

    # Groww-style header: name, big price and today's change in rupees and percent
    prev = price / (1 + day_pct / 100) if day_pct > -99 else price
    cls, arrow = ("up", "▲") if day_pct >= 0 else ("dn", "▼")
    sector = " · ".join(x for x in (fund.get("sector"), fund.get("industry")) if x)
    st.markdown(f'<div class="px-head"><div class="px-name">{html.escape(pick)}</div>'
                + (f'<div class="px-sec">{html.escape(sector)}</div>' if sector else "")
                + f'<div class="px-row"><span class="px-price">₹{price:,.2f}</span>'
                f'<span class="px-chg {cls}">{arrow} {price - prev:+,.2f} ({day_pct:+.2f}%)</span></div>'
                '<div class="px-sub">1 day change vs previous close</div></div>', unsafe_allow_html=True)

    rng = st.pills("Time range", list(RANGES), selection_mode="single", default="1M", key="range",
                   label_visibility="collapsed") or "1M"
    left, right = st.columns([1, 2])
    kind = left.pills("Chart type", ["Line", "Candles"], selection_mode="single", default="Line", key="ctype",
                      label_visibility="collapsed") or "Line"
    ind = right.pills("Indicators", ["Volume", "SMA 20", "SMA 50"], selection_mode="multi", default=["Volume"], key="ind",
                      label_visibility="collapsed") or []
    period, interval = RANGES[rng]
    df = load_ohlc(ticker, period, interval)
    if df is None:
        st.info("Price history isn't available for this range right now. Try another range.")
    else:
        intraday = interval not in ("1d", "1wk")
        moves = [] if intraday else big_moves(df, weekly=interval == "1wk")
        heads: dict = {}
        if moves:
            with st.spinner("Looking up why it moved…"):
                heads = {m[0]: move_headline(pick, m[0].strftime("%Y-%m-%d")) for m in moves}
        first, last = float(df["Close"].iloc[0]), float(df["Close"].iloc[-1])
        ref = prev if rng == "1D" else first  # dotted baseline: previous close for 1D, start of range otherwise
        fig = build_chart(df, pick, kind, intraday, interval, moves, heads, ref,
                          "Volume" in ind, {int(i.split()[1]) for i in ind if i.startswith("SMA")})
        st.plotly_chart(fig, **PLOT_KW, config={"displayModeBar": False})
        # 1D uses the same previous-close figure as the header, so the two percentages always agree
        r_pct = day_pct if rng == "1D" else (last / first - 1) * 100
        r_chg = (price - prev) if rng == "1D" else last - first
        stat_grid([(f"{rng} return", f"{'+' if r_chg >= 0 else '−'}₹{abs(r_chg):,.2f}", r_pct,
                    "Price change over the selected range."),
                   (f"{rng} high", f"₹{df['High'].max():,.2f}", None, "Highest price in this range."),
                   (f"{rng} low", f"₹{df['Low'].min():,.2f}", None, "Lowest price in this range.")])
        if moves:
            st.markdown("**⚡ Biggest moves and what was in the news**")
            for ts, _, pct in reversed(moves):
                head = heads.get(ts)
                label = f"{ts:%d %b %Y} · {'▲' if pct > 0 else '▼'} {pct:+.1f}%"
                if head:
                    st.markdown(f"- **{label}**: [{md_safe(head['title'])}]({safe_url(head['link'])})  \n"
                                f"  <small>{md_safe(head['publisher'])}</small>", unsafe_allow_html=True)
                else:
                    st.markdown(f"- **{label}**: no matching headline found from a trusted publisher")
            st.caption("Diamonds on the chart mark these days. The headline is the top news result around that date, "
                       "so it may not be the real cause. Please open the article to check.")
        elif not intraday:
            st.caption("No unusually big single moves in this range.")

    analysis_card(price, fund, day)

    related = [s for s in stories if pick in s["tags"]][:3]
    st.markdown("**Latest news on this company**" if related else "No recent headlines mention this company.")
    for s in related:
        st.markdown(f"- [{md_safe(s['title'])}]({safe_url(s['link'])})  \n  <small>{md_safe(s['source'])} · {time_ago(s['ts'])}</small>",
                    unsafe_allow_html=True)


# ------------------------------------------------ dividends, splits and bonus
NSE_PAGE = "https://www.nseindia.com/companies-listing/corporate-filings-actions"
NSE_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
               "Accept": "application/json,text/plain,*/*", "Accept-Language": "en-US,en;q=0.9", "Referer": NSE_PAGE}


def _nse_date(text) -> date | None:
    try:
        return datetime.strptime(str(text).strip(), "%d-%b-%Y").date()
    except Exception:
        return None


def _action_kind(subject: str) -> str | None:
    low = subject.lower()
    if "bonus" in low:
        return "Bonus"
    if "split" in low or "sub-division" in low or "sub division" in low:
        return "Split"
    if "dividend" in low:
        return "Dividend"
    return None


@st.cache_data(ttl=1800, show_spinner=False)
def load_corporate_actions() -> list[dict]:
    """Upcoming dividends, splits and bonus issues from the NSE (next 45 days)."""
    today = datetime.now(IST).date()
    url = ("https://www.nseindia.com/api/corporates-corporateActions?index=equities"
           f"&from_date={today:%d-%m-%Y}&to_date={today + timedelta(days=45):%d-%m-%Y}")
    out: list[dict] = []
    try:
        session = requests.Session()
        session.headers.update(NSE_HEADERS)
        session.get("https://www.nseindia.com", timeout=6)  # NSE needs this first to hand out cookies
        resp = session.get(url, timeout=10)
        resp.raise_for_status()
        for item in resp.json():
            subject = clean_text(item.get("subject", ""))
            kind, ex = _action_kind(subject), _nse_date(item.get("exDate"))
            if kind and ex and ex >= today:
                out.append({"company": item.get("comp") or item.get("symbol") or "?", "symbol": item.get("symbol", ""),
                            "kind": kind, "detail": subject, "ex": ex, "record": _nse_date(item.get("recDate"))})
    except Exception as exc:
        log.warning("NSE corporate actions failed: %s", exc)
    return sorted(out, key=lambda a: (a["ex"], a["company"]))


@st.cache_data(ttl=3600, show_spinner=False)
def load_dividend_backup() -> list[dict]:
    """Backup route: next ex-dividend dates of the large companies tracked here (dividends only)."""
    today = datetime.now(IST).date()

    def one(item):
        name, (tk, _) = item
        try:
            ex = yf.Ticker(tk).calendar.get("Ex-Dividend Date")
            ex = ex.date() if isinstance(ex, datetime) else ex
            if isinstance(ex, date) and ex >= today:
                return {"company": name, "symbol": tk.replace(".NS", ""), "kind": "Dividend",
                        "detail": "Dividend (check the company's website for the amount)", "ex": ex, "record": None}
        except Exception:
            pass
        return None

    with ThreadPoolExecutor(max_workers=8) as pool:
        return sorted([r for r in pool.map(one, COMPANIES.items()) if r], key=lambda a: a["ex"])


def corporate_tab() -> None:
    st.subheader("📅 Upcoming dividends, splits and bonus issues")
    st.caption("Ex-date: you must already own the shares before this date to receive the benefit. "
               "Always confirm on the official exchange website before acting.")
    actions, source = load_corporate_actions(), "NSE India"
    if not actions:
        st.warning("Couldn't load the NSE list right now. This free source sometimes blocks cloud apps.")
        a, b = st.columns(2)
        a.button("🔄 Try again", on_click=load_corporate_actions.clear, key="ca_retry")
        if b.button("Show dividends from a backup source", key="ca_backup"):
            st.session_state["ca_use_backup"] = True
        st.link_button("Open the official NSE page ↗", NSE_PAGE)
        if st.session_state.get("ca_use_backup"):
            actions, source = load_dividend_backup(), "Yahoo Finance (dividends of the large companies tracked here)"
        if not actions:
            return
    kind = st.pills("Type", ["All", "Dividend", "Split", "Bonus"], selection_mode="single", default="All", key="ca_kind") or "All"
    q = st.text_input("Search company", key="ca_q", placeholder="🔎 Search a company or symbol", label_visibility="collapsed").strip().lower()
    today = datetime.now(IST).date()
    shown = [a for a in actions if (kind == "All" or a["kind"] == kind) and (not q or q in f"{a['company']} {a['symbol']}".lower())]
    st.caption(f"{len(shown)} upcoming · source: {source}")
    badge = {"Dividend": "green", "Split": "orange", "Bonus": "violet"}
    for i, a in enumerate(shown[:60]):
        days = (a["ex"] - today).days
        when = "today" if days == 0 else "tomorrow" if days == 1 else f"in {days} days"
        with st.container(border=True, key=f"card_ca_{i}"):
            st.markdown(f"**{md_safe(a['company'])}** :{badge[a['kind']]}-badge[{a['kind']}]")
            st.markdown(md_safe(a["detail"]))
            rec = f" · Record date {a['record']:%d %b %Y}" if a["record"] else ""
            st.caption(f"Ex-date {a['ex']:%d %b %Y} ({when}){rec}")
    if len(shown) > 60:
        st.caption("Showing the first 60. Use the search box to narrow it down.")


# ------------------------------------------------------------ financial terms
TERMS_PER_DAY = 10


def terms_for(day: date) -> list[dict]:
    """Today's 10 terms. The list is walked in a fixed order, so nothing repeats until every block has been shown."""
    days = len(TERMS) // TERMS_PER_DAY
    if not days:
        return []
    start = (day.toordinal() % days) * TERMS_PER_DAY
    return TERMS[start:start + TERMS_PER_DAY]


def term_block(i: int, t: dict) -> None:
    st.markdown(f"**{i}. {md_safe(t['term'])}** :blue-badge[{md_safe(t['cat'])}]  \n{md_safe(t['meaning'])}  \n"
                f"*Example: {md_safe(t['example'])}*")


def terms_tab(stories: list[dict]) -> None:
    days = len(TERMS) // TERMS_PER_DAY
    if not days:
        st.info("The terms list wasn't found. Upload terms.py next to app.py in your GitHub repo.")
        return
    today = datetime.now(IST).date()
    st.subheader(f"🧠 10 terms of the day · {today:%A, %d %B %Y}")
    st.caption(f"{len(TERMS)} unique terms, shown in a fixed order, so nothing repeats for {days} days.")
    for i, t in enumerate(terms_for(today), 1):
        term_block(i, t)

    counts, meaning = Counter(), {}
    for s in stories[:100]:
        for name, m in glossary_hits(f"{s['title']} {s['summary']}"):
            counts[name] += 1
            meaning[name] = m
    if counts:
        st.subheader("📰 Terms in today's news")
        for name, n in counts.most_common(6):
            st.markdown(f"**{md_safe(name)}**: {md_safe(meaning[name])}  \n<small>in {n} stor{'y' if n == 1 else 'ies'}</small>",
                        unsafe_allow_html=True)

    with st.expander("⏮ Previous days"):
        back = st.slider("Days back", 1, 7, 1, key="terms_back")
        day = today - timedelta(days=back)
        st.markdown(f"**{day:%A, %d %B}**")
        for i, t in enumerate(terms_for(day), 1):
            term_block(i, t)
    with st.expander(f"📖 Browse all {len(TERMS)} terms"):
        a, b = st.columns([2, 1])
        q = a.text_input("Search terms", key="terms_q", placeholder="🔎 Search a term").strip().lower()
        cat = b.selectbox("Topic", ["All"] + sorted({t["cat"] for t in TERMS}), key="terms_cat")
        hits = [t for t in sorted(TERMS, key=lambda t: t["term"].lower())
                if (cat == "All" or t["cat"] == cat) and (not q or q in f"{t['term']} {t['meaning']}".lower())]
        st.caption(f"{len(hits)} matching terms" + (" (showing the first 40)" if len(hits) > 40 else ""))
        for i, t in enumerate(hits[:40], 1):
            term_block(i, t)


def focus_tab(stories: list[dict], prices: dict) -> None:
    by_stock: dict[str, list[dict]] = {}
    for s in stories:
        for tag in s["tags"]:
            by_stock.setdefault(tag, []).append(s)
    if not by_stock:
        st.info("No company mentions in the loaded stories yet.")
        return
    for name, group in sorted(by_stock.items(), key=lambda kv: len(kv[1]), reverse=True)[:8]:
        with st.container(border=True, key=f"card_focus_{name}"):
            st.markdown(f"**{md_safe(name)}** · {len(group)} headline{'s' if len(group) != 1 else ''}")
            px = prices.get(COMPANIES[name][0])
            if px:
                st.markdown(f"₹{px[0]:,.2f} :{'green' if px[1] > 0 else 'red'}[{px[1]:+.2f}%]")
            for s in group[:3]:
                st.markdown(f"- [{md_safe(s['title'])}]({safe_url(s['link'])})  \n  <small>{md_safe(s['source'])} · {time_ago(s['ts'])}</small>",
                            unsafe_allow_html=True)


def stat_grid(items: list[tuple]) -> None:
    """Responsive tiles: 4 across on a laptop, 2 across on a phone. items = (label, value, pct change or None, tooltip)."""
    cells = []
    for label, value, pct, tip in items:
        delta = ""
        if pct is not None:
            delta = f'<div class="d {"up" if pct >= 0 else "dn"}">{"▲" if pct >= 0 else "▼"} {pct:+.2f}%</div>'
        cells.append(f'<div class="stat" title="{html.escape(tip, quote=True)}"><div class="l">{html.escape(label)}</div>'
                     f'<div class="v">{html.escape(value)}</div>{delta}</div>')
    st.markdown(f'<div class="stat-grid">{"".join(cells)}</div>', unsafe_allow_html=True)


def metrics_row(prices: dict) -> None:
    stat_grid([(label, f"{v[0]:,.2f}" if v else "—", v[1] if v else None,
                "Change vs previous close. Green = up, red = down." if v else "Data unavailable right now.")
               for label, tk in INDICES.items() for v in [prices.get(tk)]])


def price_status() -> str:
    ts, open_ = load_data_time(), market_status().startswith("Market open")
    if not ts:
        return market_status()
    lag = (datetime.now(IST) - ts).total_seconds() / 60
    note = f" (about {lag:.0f} min behind the live exchange feed)" if open_ and lag > 2 else ""
    return f"Latest price data: {ts:%H:%M} IST{note} · {market_status()}"


@st.fragment(run_every=f"{PRICE_REFRESH}s")
def price_bar() -> None:
    prices = load_prices(all_tickers())
    metrics_row(prices)
    st.caption(price_status() + f" · updates every {PRICE_REFRESH} sec")
    mood_bar(mover_rows(prices))


@st.fragment(run_every=f"{NEWS_REFRESH}s")
def news_section() -> None:
    stories, failed, fetched_at = load_news()
    st.caption(f"News updated {fetched_at:%H:%M:%S} IST · refreshes every {NEWS_REFRESH // 60} min · trusted sources only")
    if failed:
        st.caption(f"⚠️ Some sources did not respond ({', '.join(failed)}). Showing the rest.")
    if not stories:
        st.error("Couldn't load any news right now. Please tap Refresh now in a minute.")
        return
    news_tab(apply_filters(stories)[:MAX_STORIES], len(stories))


@st.fragment(run_every=f"{PRICE_REFRESH}s")
def movers_section() -> None:
    movers_tab(mover_rows(load_prices(all_tickers())), load_news()[0])
    st.caption(price_status())


@st.fragment(run_every="60s")
def focus_section() -> None:
    focus_tab(load_news()[0], load_prices(all_tickers()))


DISCLAIMER = """**Disclaimer**

Intellics is a student learning project made for educational purposes only. Nothing on this page is investment, financial, legal or tax advice, and nothing here is a recommendation or an offer to buy, sell or hold any security. The creators are not SEBI-registered investment advisers or research analysts.

- **Prices and data** come from free third-party sources (Yahoo Finance). They may be delayed, incomplete or wrong, and may differ from the exchange, your broker or other apps. Always check the official NSE/BSE data or your broker before making any decision.
- **News** belongs to its publishers and is linked, not reproduced. The short summaries are generated automatically from each headline and preview (not the full article), so they can miss details or contain mistakes. Please open the original article.
- **Investing in shares carries risk,** including loss of money. Past performance does not guarantee future results. Please speak to a SEBI-registered adviser before investing.
- This project is provided as is, without any guarantee, and the creators accept no liability for any loss arising from its use."""


def main() -> None:
    init_state()
    inject_css()
    video_background()
    header()
    filter_bar()
    price_bar()
    t_news, t_movers, t_focus, t_actions, t_terms = st.tabs(
        ["📰 News", "📈 Gainers & losers", "🔥 Stocks in focus", "📅 Dividends & splits", "📚 Financial terms"])
    with t_news:
        news_section()
    with t_movers:
        movers_section()
    with t_focus:
        focus_section()
    with t_actions:
        corporate_tab()
    with t_terms:
        terms_tab(load_news()[0])
    st.divider()
    st.caption(DISCLAIMER)
    st.caption(f"{ORG_NAME} {VERSION}")
    if FEEDBACK_URL:
        st.link_button("Found a problem? Tell us", FEEDBACK_URL)


main()
