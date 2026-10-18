"""Intellics: config module (split out of app.py)."""
from __future__ import annotations
from pathlib import Path
from zoneinfo import ZoneInfo
import logging
import re
from datetime import timezone
import urllib.parse

from companies import COMPANIES
import streamlit as st


try:
    from terms import TERMS  # terms.py must sit next to app.py
except Exception:  # keep the app alive even if the file is missing
    TERMS = []


# ----------------------------------------------------------------- settings
VERSION = "1.7 beta"


NEWS_REFRESH = 120   # seconds between news refreshes


PRICE_REFRESH = 60   # seconds between price refreshes (60 because many companies are tracked)


MAX_STORIES = 40


FEED_DEADLINE = 14   # seconds: stop waiting for slow news feeds after this long


SUMMARY_WAIT = 6     # seconds to wait for AI summaries before showing the basic ones


FAIL_PAUSE = 120     # seconds to leave a failing free source alone before trying it again


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
    "hindu businessline", "businessline", "hindustan times", "news18", "cnbctv18", "cnbc-tv18", "cnbc tv18",
    "dalal street investment journal", "dalal street journal", "dsij", "hdfc sky",
    "reuters", "financial express", "ndtv profit",
}


def trusted_publisher(name: str) -> bool:
    n = re.sub(r"\.(com|in|co\.in)$", "", name.strip().lower())  # "Moneycontrol.com" -> "moneycontrol"
    return re.sub(r"^the\s+", "", n) in TRUSTED_PUBLISHERS


INDICES = {"Sensex": "^BSESN", "Nifty 50": "^NSEI", "Brent crude (USD/bbl)": "BZ=F", "Gold (USD/oz)": "GC=F"}


# COMPANIES (name -> (Yahoo ticker, alias patterns)) and SECTORS now come from companies.py
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


def _compile(alias: str) -> re.Pattern:
    base = alias.split("(")[0]
    return re.compile(rf"(?<![A-Za-z0-9]){alias}(?![A-Za-z0-9])", 0 if base.isupper() and len(base) <= 5 else re.I)


PATTERNS = {n: [_compile(a) for a in als] for n, (_, als) in COMPANIES.items()}


TOPIC_PATTERNS = {t: re.compile(r"\b(" + "|".join(map(re.escape, kw)) + r")\b", re.I) for t, kw in TOPICS.items()}


CASE_SENSITIVE = {"FII / FPI", "GDP", "IPO", "SEBI", "RBI", "EBITDA", "SMA", "CASA", "NPA", "Fed", "GST", "Quarter (Q1-Q4)"}


GLOSS_PATTERNS = [(n, re.compile(rf"(?<![A-Za-z0-9])(?:{p})(?![A-Za-z0-9])", 0 if n in CASE_SENSITIVE else re.I), m)
                  for n, p, m in GLOSSARY]
