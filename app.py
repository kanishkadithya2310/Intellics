"""Intellics v1.0 beta: Indian markets news, explained simply.

- Animated background (optional photo)
- Every article gets a 3-4 sentence plain-English summary (free Groq AI, with an
  automatic no-AI fallback so no article is ever left without one)
- Prices refresh every 30 seconds and show the time of the latest data point
- Top gainers & losers tab with an interactive company explorer (range buttons, candles,
  "why it moved" headlines on big days, and a quick analysis card: P/E, debt to equity, ROE...)
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
import plotly.graph_objects as go
import requests
import streamlit as st
import yfinance as yf
from PIL import Image

try:
    from terms import TERMS  # terms.py must sit next to app.py
except Exception:  # keep the app alive even if the file is missing
    TERMS = []

# ----------------------------------------------------------------- settings
VERSION = "1.1 beta"
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

# Replace with the feed URLs already used in your app if they differ.
SOURCES = {
    "Economic Times": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "Moneycontrol": "https://www.moneycontrol.com/rss/MCtopnews.xml",
    "Mint": "https://www.livemint.com/rss/markets",
    "Business Standard": "https://www.business-standard.com/rss/markets-106.rss",
    "BusinessLine": "https://www.thehindubusinessline.com/markets/feeder/default.rss",
    "Google News": "https://news.google.com/rss/search?q=Sensex+OR+Nifty+OR+RBI+when:1d&hl=en-IN&gl=IN&ceid=IN:en",
}
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
    if source == "Google News" and " - " in title:
        title, publisher = title.rsplit(" - ", 1)
        shown = f"Google News ({publisher})"
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
    name, url = item
    try:
        resp = requests.get(url, headers=HEADERS, timeout=8)
        resp.raise_for_status()
        return name, feedparser.parse(resp.content).entries, None
    except Exception as exc:
        log.warning("Feed failed: %s (%s)", name, exc)
        return name, [], str(exc)


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
    with ThreadPoolExecutor(max_workers=6) as pool:
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
@media (max-width:640px){{.hero-title{{font-size:1.25rem;letter-spacing:.06em}}.brand img{{height:56px!important;width:56px!important}}
.block-container{{padding-left:.9rem;padding-right:.9rem}}.stat-grid{{grid-template-columns:repeat(2,1fr)}}.stat .v{{font-size:1.1rem}}}}
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
    fig = go.Figure(go.Bar(x=[r[3] for r in shown][::-1], y=[r[0] for r in shown][::-1], orientation="h",
                           marker_color=["#22c55e" if r[3] >= 0 else "#ef4444" for r in shown][::-1],
                           text=[f"{r[3]:+.2f}%" for r in shown][::-1], textposition="outside",
                           hovertemplate="%{y}: %{x:+.2f}%<extra></extra>"))
    fig.update_layout(height=440, margin=dict(l=0, r=30, t=10, b=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font_color="#e5e7eb", xaxis_title="% change vs previous close", dragmode=False)
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
RANGES = {"1D": ("1d", "5m"), "5D": ("5d", "15m"), "1M": ("1mo", "1d"),
          "6M": ("6mo", "1d"), "1Y": ("1y", "1d"), "5Y": ("5y", "1wk")}


@st.cache_data(ttl=300, show_spinner=False)
def load_ohlc(ticker: str, period: str, interval: str):
    try:
        df = yf.Ticker(ticker).history(period=period, interval=interval)[["Open", "High", "Low", "Close"]].dropna()
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
    """Top news result about a company around a given date (Google News search by date)."""
    d = datetime.strptime(day, "%Y-%m-%d").date()
    query = f'"{name}" (shares OR stock OR results) after:{d - timedelta(days=1)} before:{d + timedelta(days=2)}'
    url = "https://news.google.com/rss/search?" + urllib.parse.urlencode(
        {"q": query, "hl": "en-IN", "gl": "IN", "ceid": "IN:en"})
    try:
        resp = requests.get(url, headers=HEADERS, timeout=8)
        resp.raise_for_status()
        for entry in feedparser.parse(resp.content).entries[:1]:
            title, publisher = clean_text(entry.get("title", "")), ""
            if " - " in title:
                title, publisher = title.rsplit(" - ", 1)
            if title and entry.get("link"):
                return {"title": title, "publisher": publisher, "link": entry["link"]}
    except Exception as exc:
        log.warning("Move headline failed (%s, %s): %s", name, day, exc)
    return None


@st.cache_data(ttl=3600, show_spinner=False)
def load_fundamentals(ticker: str) -> dict:
    keys = ("trailingPE", "forwardPE", "priceToBook", "debtToEquity", "returnOnEquity", "profitMargins", "marketCap",
            "fiftyTwoWeekHigh", "fiftyTwoWeekLow", "dividendRate", "trailingEps", "sector", "industry")
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


def _num(v, suffix: str = "", digits: int = 1) -> str:
    return "—" if v is None else f"{v:,.{digits}f}{suffix}"


def _crore(v) -> str:
    if not v:
        return "—"
    cr = v / 1e7
    return f"₹{cr / 1e5:,.2f} lakh cr" if cr >= 1e5 else f"₹{cr:,.0f} cr"


def analysis_card(price: float, f: dict) -> None:
    st.markdown("**📊 Quick analysis**")
    if not f:
        st.info("Company numbers aren't available right now. Please try again in a few minutes.")
        return
    de, roe, pm = f.get("debtToEquity"), f.get("returnOnEquity"), f.get("profitMargins")
    de = de / 100 if de is not None else None      # Yahoo gives debt/equity as a percentage
    roe = roe * 100 if roe is not None else None
    pm = pm * 100 if pm is not None else None
    dy = f["dividendRate"] / price * 100 if f.get("dividendRate") and price else None
    eps = f.get("trailingEps")
    stat_grid([
        ("Market cap", _crore(f.get("marketCap")), None, "The total value of the company on the stock market."),
        ("P/E ratio", _num(f.get("trailingPE"), "x"), None,
         "Share price divided by yearly profit per share. A P/E of 20 means investors pay Rs 20 for every Rs 1 of yearly profit. Compare it with similar companies."),
        ("Price to book", _num(f.get("priceToBook"), "x", 2), None,
         "Share price compared with the company's book value (assets minus debts) per share."),
        ("Debt to equity", _num(de, "x", 2), None,
         "How much the company has borrowed for every Rs 1 of its own money. Lower usually means less risk. Not meaningful for banks."),
        ("Return on equity", _num(roe, "%"), None,
         "Profit earned on shareholders' money. Higher usually means the company uses money well."),
        ("Profit margin", _num(pm, "%"), None, "The share of sales the company keeps as profit."),
        ("Dividend yield", _num(dy, "%", 2), None, "Yearly dividend as a percentage of the share price."),
        ("EPS (yearly)", "—" if eps is None else f"₹{eps:,.2f}", None, "Profit earned per share over the last year."),
    ])
    lo, hi = f.get("fiftyTwoWeekLow"), f.get("fiftyTwoWeekHigh")
    if lo and hi and hi > lo and price:
        st.caption(f"52-week range: ₹{lo:,.2f} (low) to ₹{hi:,.2f} (high)")
        st.progress(float(min(max((price - lo) / (hi - lo), 0.0), 1.0)))
    if f.get("sector"):
        st.caption(f"Sector: {f['sector']}" + (f" · {f['industry']}" if f.get("industry") else ""))
    with st.expander("How to read these numbers"):
        st.markdown("- **P/E**: lower can mean cheaper, higher can mean investors expect growth. Compare within the same industry.\n"
                    "- **Debt to equity**: above 1 means more borrowed money than own money (normal for banks and finance firms).\n"
                    "- **Return on equity**: 15% or more is often seen as good.\n"
                    "- **52-week bar**: the closer to the right, the closer the price is to its yearly high.")
    st.caption("Numbers come from Yahoo Finance and can be missing or out of date. They are for learning, not advice to buy or sell.")


def build_chart(df, name: str, kind: str, intraday: bool, moves: list, heads: dict):
    up = float(df["Close"].iloc[-1]) >= float(df["Close"].iloc[0])
    color, fill = ("#22c55e", "rgba(34,197,94,.12)") if up else ("#ef4444", "rgba(239,68,68,.12)")
    when = "%{x|%d %b %H:%M}" if intraday else "%{x|%d %b %Y}"
    if kind == "Candles":
        fig = go.Figure(go.Candlestick(x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
                                       increasing_line_color="#22c55e", decreasing_line_color="#ef4444", name=name))
    else:
        fig = go.Figure(go.Scatter(x=df.index, y=df["Close"], mode="lines", name=name, line=dict(color=color, width=2.5),
                                   fill="tozeroy", fillcolor=fill, hovertemplate=f"{when}: ₹%{{y:,.2f}}<extra></extra>"))
    if moves:
        text = []
        for ts, _, pct in moves:
            head = heads.get(ts)
            line = f"{ts:%d %b}: {pct:+.1f}%"
            if head:
                line += "<br>" + textwrap.fill(head["title"], 42).replace("\n", "<br>")
            text.append(line)
        fig.add_trace(go.Scatter(x=[m[0] for m in moves], y=[m[1] for m in moves], mode="markers", showlegend=False,
                                 marker=dict(size=13, symbol="diamond", line=dict(width=1.5, color="white"),
                                             color=["#22c55e" if m[2] > 0 else "#ef4444" for m in moves]),
                                 text=text, hovertemplate="%{text}<extra></extra>"))
    lo, hi = float(df["Low"].min()), float(df["High"].max())
    pad = (hi - lo) * 0.06 or 1
    breaks = [dict(bounds=["sat", "mon"])]
    if intraday:
        breaks.append(dict(bounds=[15.5, 9.25], pattern="hour"))
    fig.update_xaxes(rangebreaks=breaks, rangeslider_visible=False)
    fig.update_yaxes(range=[lo - pad, hi + pad])
    fig.update_layout(height=340, margin=dict(l=0, r=0, t=10, b=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font_color="#e5e7eb", dragmode=False, hovermode="closest" if moves else "x", hoverdistance=40)
    return fig


def company_explorer(rows: list, stories: list[dict]) -> None:
    st.subheader("🔍 Explore a company")
    pick = st.selectbox("Search or pick a company", [r[0] for r in rows], key="explore")
    row = next(r for r in rows if r[0] == pick)
    ticker, price = row[1], row[2]
    stat_grid([(pick, f"₹{price:,.2f}", row[3], "Latest price and change versus the previous close.")])

    left, right = st.columns([3, 2])
    rng = left.pills("Time range", list(RANGES), selection_mode="single", default="1M", key="range",
                     label_visibility="collapsed") or "1M"
    kind = right.pills("Chart type", ["Line", "Candles"], selection_mode="single", default="Line", key="ctype",
                       label_visibility="collapsed") or "Line"
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
        st.plotly_chart(build_chart(df, pick, kind, intraday, moves, heads), **PLOT_KW, config={"displayModeBar": False})
        first, last = float(df["Close"].iloc[0]), float(df["Close"].iloc[-1])
        stat_grid([(f"{rng} change", f"{(last / first - 1) * 100:+.2f}%", None, "Price change over the selected range."),
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
                    st.markdown(f"- **{label}**: no matching headline found")
            st.caption("Diamonds on the chart mark these days. The headline is the top news result around that date, "
                       "so it may not be the real cause. Please open the article to check.")
        elif not intraday:
            st.caption("No unusually big single moves in this range.")

    with st.spinner("Loading company numbers…"):
        fund = load_fundamentals(ticker)
    analysis_card(price, fund)

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
            delta = f'<div class="d {"up" if pct >= 0 else "dn"}">{"▲" if pct >= 0 else "▼"} {abs(pct):.2f}%</div>'
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
    st.caption(f"News updated {fetched_at:%H:%M:%S} IST · refreshes every {NEWS_REFRESH // 60} min")
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
