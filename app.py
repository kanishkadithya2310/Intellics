"""Intellics Daily Finance Desk v2 - live news, top movers, stocks in focus, longer previews.
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
REFRESH_SECONDS = 120
MAX_ITEMS = 40
SUMMARY_CHARS = 600
IST = pytz.timezone("Asia/Kolkata")
UA = {"User-Agent": "Mozilla/5.0 (compatible; IntellicsNewsDesk/2.0)"}

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

# name -> (NSE symbol, [aliases used to spot the company in headlines])
STOCKS = {
    "Reliance": ("RELIANCE.NS", ["Reliance", "RIL"]), "TCS": ("TCS.NS", ["TCS"]),
    "HDFC Bank": ("HDFCBANK.NS", ["HDFC Bank"]), "Infosys": ("INFY.NS", ["Infosys"]),
    "ICICI Bank": ("ICICIBANK.NS", ["ICICI Bank"]), "SBI": ("SBIN.NS", ["SBI", "State Bank of India"]),
    "Bharti Airtel": ("BHARTIARTL.NS", ["Airtel"]), "ITC": ("ITC.NS", ["ITC"]),
    "L&T": ("LT.NS", ["L&T", "Larsen"]), "Axis Bank": ("AXISBANK.NS", ["Axis Bank"]),
    "Kotak Bank": ("KOTAKBANK.NS", ["Kotak"]), "Maruti": ("MARUTI.NS", ["Maruti"]),
    "Tata Steel": ("TATASTEEL.NS", ["Tata Steel"]), "Sun Pharma": ("SUNPHARMA.NS", ["Sun Pharma"]),
    "Titan": ("TITAN.NS", ["Titan"]), "Asian Paints": ("ASIANPAINT.NS", ["Asian Paints"]),
    "Bajaj Finance": ("BAJFINANCE.NS", ["Bajaj Finance"]), "Wipro": ("WIPRO.NS", ["Wipro"]),
    "HCL Tech": ("HCLTECH.NS", ["HCLTech", "HCL Tech"]), "Adani Ports": ("ADANIPORTS.NS", ["Adani Ports"]),
    "Adani Enterprises": ("ADANIENT.NS", ["Adani Enterprises"]), "ONGC": ("ONGC.NS", ["ONGC"]),
    "NTPC": ("NTPC.NS", ["NTPC"]), "Power Grid": ("POWERGRID.NS", ["Power Grid"]),
    "M&M": ("M&M.NS", ["M&M", "Mahindra & Mahindra"]), "UltraTech": ("ULTRACEMCO.NS", ["UltraTech"]),
    "Nestle India": ("NESTLEIND.NS", ["Nestle"]), "HUL": ("HINDUNILVR.NS", ["HUL", "Hindustan Unilever"]),
    "Tech Mahindra": ("TECHM.NS", ["Tech Mahindra"]), "JSW Steel": ("JSWSTEEL.NS", ["JSW Steel"]),
    "Coal India": ("COALINDIA.NS", ["Coal India"]), "Hindalco": ("HINDALCO.NS", ["Hindalco"]),
    "IndusInd Bank": ("INDUSINDBK.NS", ["IndusInd"]), "Eicher Motors": ("EICHERMOT.NS", ["Eicher"]),
    "Cipla": ("CIPLA.NS", ["Cipla"]), "Dr Reddy's": ("DRREDDY.NS", ["Dr Reddy"]),
    "Britannia": ("BRITANNIA.NS", ["Britannia"]), "Grasim": ("GRASIM.NS", ["Grasim"]),
    "Apollo Hospitals": ("APOLLOHOSP.NS", ["Apollo Hospitals"]), "Bajaj Finserv": ("BAJAJFINSV.NS", ["Bajaj Finserv"]),
    "BPCL": ("BPCL.NS", ["BPCL"]), "Trent": ("TRENT.NS", ["Trent"]),
    "Shriram Finance": ("SHRIRAMFIN.NS", ["Shriram Finance"]), "SBI Life": ("SBILIFE.NS", ["SBI Life"]),
    "HDFC Life": ("HDFCLIFE.NS", ["HDFC Life"]), "Tata Consumer": ("TATACONSUM.NS", ["Tata Consumer"]),
    "Hero MotoCorp": ("HEROMOTOCO.NS", ["Hero MotoCorp"]), "BEL": ("BEL.NS", ["BEL", "Bharat Electronics"]),
    "Jio Financial": ("JIOFIN.NS", ["Jio Financial"]),
}
PATTERNS = []
for _name, (_sym, _aliases) in STOCKS.items():
    for _a in _aliases:
        flag = 0 if (_a.isupper() and len(_a) <= 4) else re.I   # short tickers: exact case only
        PATTERNS.append((_name, re.compile(r"(?<![A-Za-z])" + re.escape(_a) + r"(?![A-Za-z])", flag)))

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
            summary = re.sub(r"<[^>]+>", " ", html.unescape(e.get("summary", "") or e.get("description", "")))
            summary = re.sub(r"\s+", " ", summary).strip()
            out.append({"title": html.unescape(e.get("title", "")).strip(), "link": e.get("link", "#"),
                        "source": name, "when": when, "summary": summary[:SUMMARY_CHARS]})
        return name, out
    except Exception:
        return name, []


@st.cache_data(ttl=REFRESH_SECONDS, show_spinner=False)
def get_news():
    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(lambda kv: fetch_feed(*kv), FEEDS.items()))
    items, failed = [], []
    for name, rows in results:
        if not rows:
            failed.append(name)
        items += rows
    seen, unique = set(), []
    for it in sorted(items, key=lambda x: x["when"] or datetime(2000, 1, 1, tzinfo=IST), reverse=True):
        key = re.sub(r"\W+", "", it["title"].lower())[:60]
        if key and key not in seen:
            seen.add(key)
            unique.append(it)
    return unique, failed


@st.cache_data(ttl=86400, show_spinner=False)
def get_preview(url):
    """The publisher's own public description of the article (not the paywalled body)."""
    try:
        page = requests.get(url, headers=UA, timeout=6).text[:200000]
        for pat in (r'<meta[^>]+(?:property|name)=["\'](?:og:description|description)["\'][^>]*content=["\']([^"\']+)',
                    r'<meta[^>]+content=["\']([^"\']+)["\'][^>]*(?:property|name)=["\'](?:og:description|description)["\']'):
            m = re.search(pat, page, re.I)
            if m:
                return re.sub(r"\s+", " ", html.unescape(m.group(1))).strip()[:SUMMARY_CHARS]
    except Exception:
        pass
    return ""


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


@st.cache_data(ttl=REFRESH_SECONDS, show_spinner=False)
def get_movers():
    """Day change for every stock in STOCKS: {name: (price, change %)}"""
    syms = [v[0] for v in STOCKS.values()]
    try:
        close = yf.download(syms, period="5d", interval="1d", progress=False,
                            auto_adjust=True, group_by="column", threads=True)["Close"].ffill()
        last, prev = close.iloc[-1], close.iloc[-2]
    except Exception:
        return {}
    out = {}
    for name, (sym, _) in STOCKS.items():
        try:
            if sym in last and last[sym] == last[sym] and prev[sym] == prev[sym]:
                out[name] = (float(last[sym]), (float(last[sym]) / float(prev[sym]) - 1) * 100)
        except Exception:
            pass
    return out


def stocks_in_news(items):
    hits = {}
    for it in items:
        text = it["title"] + " " + it["summary"]
        for name in {n for n, p in PATTERNS if p.search(text)}:
            hits.setdefault(name, []).append(it)
    return sorted(hits.items(), key=lambda kv: -len(kv[1]))


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
st.caption("Live headlines from leading Indian business outlets, top movers and stocks in focus, "
           "refreshed automatically. Every card links to the original article.")

with st.sidebar:
    st.header("Filters")
    topic = st.radio("Topic", list(TOPICS.keys()))
    query = st.text_input("Search headlines", placeholder="e.g. RBI, Reliance, gold")
    today_only = st.checkbox("Today only", value=False)
    detailed = st.checkbox("Longer previews", value=True,
                           help="Adds the publisher's public article description when it is longer than the feed snippet.")
    source_pick = st.multiselect("Sources", list(FEEDS.keys()), default=list(FEEDS.keys()))
    if st.button("🔄 Refresh now"):
        st.cache_data.clear()
        st.rerun()
    st.caption("For learning only. Not investment advice.")


def mover_row(name, price, chg):
    c1, c2, c3 = st.columns([3, 2, 2])
    c1.write(f"**{name}**")
    c2.write(f"₹{price:,.2f}")
    c3.write(f":{'green' if chg >= 0 else 'red'}[{chg:+.2f}%]")


@st.fragment(run_every=REFRESH_SECONDS)
def desk(topic, query, today_only, detailed, source_pick):
    cols = st.columns(len(TICKERS))
    for col, (label, price, chg) in zip(cols, get_tiles()):
        if price is None:
            col.metric(label, "n/a")
        else:
            col.metric(label, f"{price:,.2f}", f"{chg:+.2f}%",
                       delta_color="inverse" if label in ("USD/INR", "Brent crude") else "normal")

    items, failed = get_news()
    movers = get_movers()
    tab_news, tab_move, tab_focus = st.tabs(["📰 News", "📈 Top gainers & losers", "🔥 Stocks in focus"])

    with tab_move:
        if not movers:
            st.info("Price data is not available right now. Try again in a minute.")
        else:
            ranked = sorted(movers.items(), key=lambda kv: kv[1][1], reverse=True)
            g, l = st.columns(2)
            with g:
                st.subheader("🟢 Best performers")
                for n, (p, c) in ranked[:5]:
                    mover_row(n, p, c)
            with l:
                st.subheader("🔴 Worst performers")
                for n, (p, c) in ranked[::-1][:5]:
                    mover_row(n, p, c)
            st.caption("Change vs previous close, among large NSE companies tracked here. "
                       "Outside market hours this shows the last session.")

    with tab_focus:
        focus = stocks_in_news(items)[:8]
        if not focus:
            st.info("No company names spotted in the latest headlines yet.")
        for name, arts in focus:
            with st.container(border=True):
                a, b = st.columns([2, 5])
                a.markdown(f"**{name}**")
                a.caption(f"{len(arts)} headline{'s' if len(arts) > 1 else ''}")
                if name in movers:
                    p, c = movers[name]
                    a.write(f"₹{p:,.2f} :{'green' if c >= 0 else 'red'}[{c:+.2f}%]")
                for it in arts[:3]:
                    b.markdown(f"- [{it['title']}]({it['link']})  \n  <small>{it['source']} · {ago(it['when'])}</small>",
                               unsafe_allow_html=True)
        st.caption("Ranked by how often a company appears in today's headlines. "
                   "'In the news' is not a buy or sell signal.")

    with tab_news:
        kws, q, today = TOPICS[topic], query.lower().strip(), datetime.now(IST).date()
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
        shown = shown[:MAX_ITEMS]
        if detailed and shown:
            with ThreadPoolExecutor(max_workers=8) as pool:
                previews = list(pool.map(lambda i: get_preview(i["link"]), shown[:15]))
        else:
            previews = []
        st.caption(f"Updated {datetime.now(IST):%H:%M:%S} IST · {len(shown)} stories · "
                   f"auto-refresh every {REFRESH_SECONDS // 60} min"
                   + (f" · unavailable right now: {', '.join(failed)}" if failed else ""))
        if not shown:
            st.info("No stories match these filters yet. Try 'All' or turn off 'Today only'.")
        for idx, it in enumerate(shown):
            text = it["summary"]
            if idx < len(previews) and len(previews[idx]) > len(text):
                text = previews[idx]
            with st.container(border=True):
                st.markdown(f"**[{it['title']}]({it['link']})**")
                st.caption(f"{it['source']} · {ago(it['when'])}")
                if text:
                    st.write(text)
                tagged = [n for n, p in PATTERNS if p.search(it["title"])]
                if tagged:
                    st.caption("Stocks mentioned: " + ", ".join(sorted(set(tagged))))


desk(topic, query, today_only, detailed, source_pick)
