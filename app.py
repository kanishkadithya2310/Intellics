"""Intellics v1.0 beta: Indian markets news, explained simply.

- Animated background (optional photo or looping hero video)
- Every article gets a 3-4 sentence plain-English summary (free Groq AI, with an
  automatic no-AI fallback so no article is ever left without one)
- Prices refresh every few seconds and show the time of the latest data point
- Top gainers & losers tab with chart, company explorer and related news
- Financial terms tab: a new term every day
"""
from __future__ import annotations

import base64
import hashlib
import html
import json
import logging
import re
import threading
import time
from functools import lru_cache
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, wait
from collections import Counter
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

# ----------------------------------------------------------------- settings
VERSION = "1.0 beta"
NEWS_REFRESH = 120   # seconds between news refreshes
PRICE_REFRESH = 5     # seconds: Sensex, Nifty, Brent, Gold (4 tickers, a light request)
COMPANY_REFRESH = 15  # seconds: the ~33 tracked companies (one bigger request)
MOVERS_REFRESH = 30   # gainers/losers page redraws slower so charts do not flicker while you use them
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
# ------------------------------------------------- Financial terms library
# One new term per day, in this fixed order, so nothing repeats until all have been shown.
# To add more: append new lines at the END of the list (this keeps past days unchanged).
START_DATE = date(2026, 10, 8)  # day 1 of the cycle
TERMS = [  # (term, category, simple meaning, example)
    ("Mutual fund", "Investing", "A pool of money from many investors, managed by a professional who buys shares, bonds or other assets.", "Priya puts ₹1,000 in a mutual fund instead of picking shares herself."),
    ("Bid and ask", "Markets", "The bid is the highest price buyers offer; the ask is the lowest price sellers will accept.", "A share shows bid ₹99.90 and ask ₹100.10."),
    ("Interest rate", "Economy", "The cost of borrowing money, or the reward for saving it, shown as a percentage per year.", "A bank offers 7% a year on a fixed deposit."),
    ("Revenue vs profit", "Company", "Revenue is all the money a company earns from sales; profit is what is left after paying all costs.", "A cafe sells ₹10 lakh of coffee (revenue) but keeps ₹1 lakh after costs (profit)."),
    ("SIP", "Investing", "Systematic Investment Plan: investing a fixed amount at regular intervals, usually every month.", "Arjun invests ₹500 on the 5th of every month."),
    ("Stop-loss", "Markets", "An order that automatically sells a share if its price falls to a level you set, to limit your loss.", "You bought at ₹100 and set a stop-loss at ₹92."),
    ("Fiscal deficit", "Economy", "When the government spends more than it earns in a year, apart from borrowing.", "If the government earns ₹90 and spends ₹100, the gap of ₹10 is the deficit."),
    ("Balance sheet", "Company", "A snapshot of what a company owns (assets), what it owes (liabilities) and what is left for its owners.", "It shows the company has ₹50 crore in assets and ₹30 crore in debts."),
    ("NAV", "Investing", "Net Asset Value: the price of one unit of a mutual fund, based on the value of everything the fund holds.", "A fund with NAV ₹25 means one unit costs ₹25."),
    ("Limit order", "Markets", "An order to buy or sell only at a price you choose, or better.", "You place a buy order at ₹95 and it fills only if the price drops that low."),
    ("Recession", "Economy", "A long period when the economy shrinks, often shown by falling GDP for two quarters in a row.", "Jobs get scarce and spending drops during a recession."),
    ("P/E ratio", "Company", "Price divided by earnings per share: how much investors pay for each rupee of a company's yearly profit.", "A P/E of 20 means investors pay ₹20 for every ₹1 of yearly profit."),
    ("Diversification", "Investing", "Spreading your money across different investments so one bad performer hurts you less.", "Holding shares, gold and bonds instead of only one stock."),
    ("Short selling", "Markets", "Selling borrowed shares in the hope of buying them back later at a lower price.", "You sell at ₹100, the price falls to ₹80, you buy back and keep the ₹20 gap."),
    ("Exchange rate", "Economy", "The price of one currency in terms of another.", "If ₹85 buys one US dollar, that is the rupee-dollar exchange rate."),
    ("Stock split", "Company", "A company divides each share into more shares. The price per share drops, but your total value stays the same.", "A 1-for-2 split turns one ₹1,000 share into two ₹500 shares."),
    ("Compounding", "Investing", "Earning returns on your earlier returns, so your money grows faster over time.", "₹1,000 at 10% becomes ₹1,100, then ₹1,210 the next year."),
    ("Trading volume", "Markets", "The number of shares traded in a period. High volume means lots of buying and selling activity.", "5 lakh shares changed hands today, more than usual."),
    ("Monetary policy", "Economy", "Steps the central bank (RBI) takes, such as changing interest rates, to control prices and support growth.", "The RBI raises rates to slow rising prices."),
    ("Net profit margin", "Company", "The percentage of sales a company keeps as profit after all costs.", "Earning ₹10 profit on ₹100 of sales is a 10% margin."),
    ("Blue-chip stock", "Investing", "A share of a large, well-established, financially strong company with a long record.", "Big household-name companies are often called blue chips."),
    ("Market order", "Markets", "An order to buy or sell right away at the best price available.", "You tap Buy and the order fills at the current price."),
    ("Trade deficit", "Economy", "When a country buys more goods from the world (imports) than it sells (exports).", "India imports ₹100 of goods and exports ₹80, so the deficit is ₹20."),
    ("EPS", "Company", "Earnings per share: a company's profit divided by its number of shares.", "A ₹100 crore profit across 10 crore shares is ₹10 EPS."),
    ("Index fund", "Investing", "A fund that simply copies an index such as the Nifty 50, usually with low fees.", "An index fund buys all 50 Nifty companies in the same proportion."),
    ("Futures", "Markets", "A contract to buy or sell something at a fixed price on a future date.", "A trader agrees today to buy crude oil at a set price in two months."),
    ("Forex reserves", "Economy", "Foreign currency and gold held by a country's central bank to pay for imports and steady the currency.", "The RBI sells dollars from its reserves to support the rupee."),
    ("Buyback", "Company", "A company buys its own shares back from investors, which reduces the number of shares in the market.", "A firm offers ₹1,200 per share to buy back 2% of its shares."),
    ("ETF", "Investing", "Exchange Traded Fund: a basket of investments that you can buy and sell on the stock exchange like a share.", "A gold ETF lets you hold gold without buying coins."),
    ("Options", "Markets", "A contract that gives you the right, but not the duty, to buy or sell at a set price before a date.", "You pay a small fee for the right to buy a share at ₹100 next month."),
    ("CRR", "Economy", "Cash Reserve Ratio: the share of deposits that banks must keep with the RBI as cash.", "If CRR is 4%, a bank with ₹100 deposits keeps ₹4 with the RBI."),
    ("Debt-to-equity ratio", "Company", "How much a company has borrowed compared with the money its owners have put in.", "₹60 of debt against ₹40 of owners' money gives a ratio of 1.5."),
    ("Asset allocation", "Investing", "How you split your money between shares, bonds, gold, cash and other assets.", "60% in shares, 30% in bonds and 10% in gold."),
    ("Derivative", "Markets", "A financial contract whose value depends on another asset, such as a share, gold or oil.", "Futures and options are derivatives."),
    ("Credit score", "Economy", "A number (such as the CIBIL score) that shows how reliably you have repaid loans.", "A high score can help you get a loan at a lower rate."),
    ("Bonus shares", "Company", "Free extra shares a company gives to its existing shareholders.", "A 1:1 bonus gives you one extra share for each share you own."),
    ("Expense ratio", "Investing", "The yearly fee a mutual fund or ETF charges, as a percentage of your money.", "A 1% expense ratio costs ₹100 a year on ₹10,000 invested."),
    ("Circuit breaker", "Markets", "A rule that pauses trading or limits price moves when prices swing too far in a day.", "Trading in a share stops for the day after it rises 20%."),
    ("EMI", "Economy", "Equated Monthly Instalment: the fixed amount you pay every month to repay a loan.", "You repay a bike loan with an EMI of ₹3,000."),
    ("Rights issue", "Company", "An offer of new shares to existing shareholders, often at a discount, to raise money.", "A company offers one new share for every five you own."),
    ("Penny stock", "Investing", "A very cheap share of a small company. These are usually risky and hard to sell.", "A ₹2 share with few buyers is a penny stock."),
    ("Margin trading", "Markets", "Borrowing money from your broker to trade more than you could with your own cash. Losses are bigger too.", "You put in ₹10,000 and trade ₹40,000 worth of shares."),
    ("Fixed deposit", "Economy", "Money you keep in a bank for a fixed time at a fixed interest rate.", "₹50,000 locked for one year at 7%."),
    ("Working capital", "Company", "The money a business needs for day-to-day running, such as paying suppliers and salaries.", "A shop needs cash to restock before sales come in."),
    ("Lock-in period", "Investing", "A time during which you cannot withdraw or sell an investment.", "Some tax-saving funds lock your money for three years."),
    ("Demat account", "Markets", "An account that holds your shares in electronic form, like a bank account for shares.", "You need a demat account to buy shares online."),
    ("Stagflation", "Economy", "A bad mix of slow growth, high unemployment and rising prices at the same time.", "Prices keep climbing while jobs get harder to find."),
    ("Cash flow", "Company", "The money moving into and out of a business over a period.", "A company can show a profit on paper yet run short of cash."),
    ("Risk appetite", "Investing", "How much loss of value you can accept in return for the chance of higher gains.", "A student with a long horizon may accept more risk than a retiree."),
    ("Settlement (T+1)", "Markets", "The time a trade takes to complete. T+1 means shares and money change hands one working day after the trade.", "Shares bought on Monday reach your demat account on Tuesday."),
    ("SLR", "Economy", "Statutory Liquidity Ratio: the share of deposits banks must hold in cash, gold or government bonds.", "A bank holds part of your deposit in safe government bonds."),
    ("Book value", "Company", "A company's net worth on paper: assets minus liabilities, often shown per share.", "A company worth ₹500 crore on paper with 10 crore shares has a book value of ₹50 per share."),
    ("Rebalancing", "Investing", "Adjusting your investments back to your planned split after prices have moved.", "Shares grew to 70% of your portfolio, so you sell some to get back to 60%."),
    ("Spread", "Markets", "The gap between the bid price and the ask price. A smaller gap usually means an easier, cheaper trade.", "Bid ₹99.90 and ask ₹100.10 give a spread of ₹0.20."),
    ("Deflation", "Economy", "A general fall in prices over time, the opposite of inflation.", "Prices drop for months, so people delay purchases."),
    ("ROE", "Company", "Return on equity: how much profit a company makes for every rupee of its owners' money.", "₹15 profit on ₹100 of owners' money is a 15% ROE."),
    ("Dividend yield", "Investing", "The yearly dividend as a percentage of the share price.", "A ₹5 dividend on a ₹100 share is a 5% yield."),
    ("Index", "Markets", "A number that tracks a group of shares to show how the market is doing, such as the Sensex or Nifty 50.", "The Nifty rising means the 50 big companies are doing well overall."),
    ("Fiscal policy", "Economy", "The government's decisions on taxes and spending to steer the economy.", "Cutting taxes to boost spending is a fiscal policy move."),
    ("Promoter holding", "Company", "The percentage of a company's shares held by its founders or owners.", "Founders own 55% of the shares, so promoter holding is 55%."),
    ("Bull market", "Investing", "A long period when prices rise and investors feel confident.", "Share prices climb for two years straight."),
    ("Rally", "Markets", "A sharp rise in prices over a short time.", "Banking shares rally after good results."),
    ("Current account deficit", "Economy", "When a country pays the world more for goods, services and income than it earns from them.", "A high oil import bill widens the deficit."),
    ("Venture capital", "Company", "Money invested in young, high-growth startups in return for part ownership.", "A fund puts ₹5 crore into a new app company for 20% of it."),
    ("Bear market", "Investing", "A long period of falling prices, usually a drop of 20% or more from a recent high.", "Shares slide for months and investors turn fearful."),
    ("Correction", "Markets", "A fall of about 10% or more from a recent high. It is often seen as a healthy pause.", "The index drops 10% after a long climb."),
    ("Collateral", "Economy", "An asset you pledge to secure a loan. The lender can take it if you do not repay.", "A home is pledged against a home loan."),
    ("Unicorn", "Company", "A startup valued at more than US$1 billion.", "A food-delivery startup valued at US$2 billion is a unicorn."),
    ("Volatility", "Investing", "How sharply and how quickly prices move up and down.", "A share that jumps 5% one day and falls 6% the next is volatile."),
    ("Support and resistance", "Markets", "Price levels where a share has often stopped falling (support) or stopped rising (resistance).", "A share keeps bouncing back up from ₹90."),
    ("Real return", "Economy", "Your investment return after taking away inflation.", "7% interest with 5% inflation is only about a 2% real return."),
    ("Bootstrapping", "Company", "Building a business using your own savings and sales, with no outside investors.", "Two friends start a design studio using their own money."),
    ("Liquidity", "Investing", "How quickly and easily something can be turned into cash without losing value.", "Shares are easier to sell than land, so they are more liquid."),
    ("Candlestick chart", "Markets", "A price chart where each bar shows the open, high, low and close for a period.", "A green candle means the price closed higher than it opened."),
    ("Credit rating", "Economy", "A grade that shows how likely a borrower is to repay its debt.", "A company with a top rating can borrow at lower interest."),
    ("Due diligence", "Company", "Carefully checking the facts and numbers before buying a company or making a big investment.", "Before a takeover, the buyer reviews all accounts and contracts."),
    ("Large-cap and small-cap", "Investing", "Cap means market value. Large-caps are big, steady companies; small-caps are smaller and riskier.", "A top bank is a large-cap; a young local firm is a small-cap."),
    ("Arbitrage", "Markets", "Earning a small, low-risk profit from a price difference for the same asset in two places.", "A share costs ₹100.00 on one exchange and ₹100.20 on another."),
    ("Disinvestment", "Economy", "The government selling part or all of its stake in a public-sector company.", "The government sells 10% of a state-owned company to the public."),
    ("Goodwill", "Company", "The extra amount paid for a business above the value of its assets, for its brand, customers and reputation.", "A buyer pays ₹120 crore for a firm whose assets are worth ₹100 crore."),
    ("Hedging", "Investing", "Making a second investment to reduce the risk of loss on the first.", "An exporter locks in an exchange rate to protect against a falling dollar."),
    ("Insider trading", "Markets", "Trading shares using important information that is not yet public. It is illegal.", "An employee buys shares before announcing the company's takeover."),
    ("Government bond (G-Sec)", "Economy", "A loan you give to the government in return for regular interest. It is generally considered very safe.", "You buy a 10-year G-Sec paying fixed interest."),
    ("Hostile takeover", "Company", "When one company tries to buy another against the wishes of its management.", "A buyer goes directly to shareholders to buy their shares."),
    ("REIT", "Investing", "Real Estate Investment Trust: lets you earn from property, such as offices, by buying units, without buying a building.", "You buy REIT units and receive a share of the rent."),
    ("Speculation", "Markets", "Taking big risks on short-term price moves, hoping for quick gains, rather than investing for the long term.", "Buying a share only because you expect it to jump tomorrow."),
    ("Subsidy", "Economy", "Money the government gives to lower the cost of something for people or businesses.", "A subsidy on cooking gas makes it cheaper for households."),
    ("ESG", "Company", "Environmental, Social and Governance: ways of judging how responsibly a company runs its business.", "Investors favour firms that cut pollution and treat workers fairly."),
    ("Income statement", "Company", "A report showing a company's sales, costs and profit over a period. It is also called the profit and loss (P&L) account.", "The quarterly results show sales up 8% and profit up 12%."),
    ("Currency depreciation", "Economy", "When a currency loses value against another. For example, the rupee weakens against the dollar.", "If the rupee falls from ₹84 to ₹86 per dollar, imports cost more."),
]
assert len({t[0] for t in TERMS}) == len(TERMS), "duplicate term in TERMS"


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


def _fetch_prices(tickers: tuple[str, ...]) -> dict[str, tuple[float, float]]:
    """ticker -> (latest price, % change vs previous close), straight from Yahoo."""
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


@st.cache_resource
def _last_good() -> dict:
    return {}


def _fetch_with_memory(tickers: tuple[str, ...]) -> dict[str, tuple[float, float]]:
    """If a quick refresh fails or is throttled, keep showing the last good price (up to 10 min) instead of going blank."""
    fresh, mem, now = _fetch_prices(tickers), _last_good(), time.time()
    for t, v in fresh.items():
        mem[t] = (v, now)
    return {t: mem[t][0] for t in tickers if t in mem and now - mem[t][1] < 600}


@st.cache_data(ttl=PRICE_REFRESH, show_spinner=False)
def load_index_prices(tickers: tuple[str, ...]):
    return _fetch_with_memory(tickers)


@st.cache_data(ttl=COMPANY_REFRESH, show_spinner=False)
def load_company_prices(tickers: tuple[str, ...]):
    return _fetch_with_memory(tickers)


def index_tickers() -> tuple[str, ...]:
    return tuple(INDICES.values())


def company_tickers() -> tuple[str, ...]:
    return tuple(t for t, _ in COMPANIES.values())


def get_prices() -> dict[str, tuple[float, float]]:
    return {**load_company_prices(company_tickers()), **load_index_prices(index_tickers())}


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
    """Time of the newest 1-minute price point Yahoo has for Reliance (backup: Nifty). Shows how fresh the data really is."""
    for symbol in ("RELIANCE.NS", "^NSEI"):
        try:
            df = yf.download(symbol, period="1d", interval="1m", progress=False, auto_adjust=False)
            if len(df):
                ts = df.index[-1]
                ts = ts.tz_localize("UTC") if ts.tzinfo is None else ts
                return ts.tz_convert(IST).to_pydatetime()
        except Exception as exc:
            log.warning("Data-time lookup failed for %s: %s", symbol, exc)
    return None


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
@media (prefers-reduced-motion:reduce){{.stApp::before{{animation:none}}div[class*="st-key-card_"]{{transition:none}}}}
</style>""", unsafe_allow_html=True)


def video_background() -> None:
    """Full-screen looping hero video behind the page. Set VIDEO_URL = "" to switch it off."""
    if not VIDEO_URL:
        return
    st.markdown(f"""<style>
html,body{{background:#0a0f1f}}
.stApp,[data-testid="stAppViewContainer"],[data-testid="stHeader"]{{background:transparent!important}}
.stApp::before{{display:none}}
.hero-video{{position:fixed;top:0;left:0;width:100vw;height:100vh;object-fit:cover;z-index:-1}}
.hero-overlay{{position:fixed;inset:0;background:rgba(10,15,31,.6);z-index:-1}}
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
    load_index_prices.clear()
    load_company_prices.clear()
    load_data_time.clear()


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

    st.subheader("🔍 Explore a company")
    pick = st.selectbox("Pick a company", [r[0] for r in rows], key="explore")
    row = next(r for r in rows if r[0] == pick)
    st.metric(pick, f"₹{row[2]:,.2f}", f"{row[3]:+.2f}%")
    hist = load_history(row[1])
    if hist is not None and len(hist) > 1:
        line = go.Figure(go.Scatter(x=hist.index, y=hist.values, mode="lines", line=dict(color="#60a5fa", width=2.5), fill="tozeroy",
                                    fillcolor="rgba(96,165,250,.12)", hovertemplate="%{x|%d %b}: ₹%{y:,.2f}<extra></extra>"))
        line.update_layout(height=260, margin=dict(l=0, r=0, t=10, b=0), paper_bgcolor="rgba(0,0,0,0)",
                           plot_bgcolor="rgba(0,0,0,0)", font_color="#e5e7eb", yaxis=dict(range=[hist.min() * .98, hist.max() * 1.02]))
        st.caption("Last month's closing price")
        st.plotly_chart(line, **PLOT_KW, config={"displayModeBar": False})
    related = [s for s in stories if pick in s["tags"]][:3]
    st.markdown("**Latest news on this company**" if related else "No recent headlines mention this company.")
    for s in related:
        st.markdown(f"- [{md_safe(s['title'])}]({safe_url(s['link'])})  \n  <small>{md_safe(s['source'])} · {time_ago(s['ts'])}</small>",
                    unsafe_allow_html=True)


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


def metrics_row(prices: dict) -> None:
    for col, (label, tk) in zip(st.columns(len(INDICES)), INDICES.items()):
        v = prices.get(tk)
        col.metric(label, f"{v[0]:,.2f}" if v else "—", f"{v[1]:+.2f}%" if v else None,
                   help="Change vs previous close. Green = up, red = down." if v else "Data unavailable right now.")


def price_status() -> str:
    ts, open_ = load_data_time(), market_status().startswith("Market open")
    if not ts:
        return market_status()
    lag = (datetime.now(IST) - ts).total_seconds() / 60
    note = f" (about {lag:.0f} min behind the live exchange feed)" if open_ and lag > 2 else ""
    return f"Latest price data: {ts:%H:%M} IST{note} · {market_status()}"


@st.fragment(run_every=f"{PRICE_REFRESH}s")
def price_bar() -> None:
    prices = get_prices()
    metrics_row(prices)
    st.caption(price_status() + f" · prices update every {PRICE_REFRESH}-{COMPANY_REFRESH} sec")
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


@st.fragment(run_every=f"{MOVERS_REFRESH}s")
def movers_section() -> None:
    movers_tab(mover_rows(get_prices()), load_news()[0])
    st.caption(price_status())


@st.fragment(run_every="60s")
def focus_section() -> None:
    focus_tab(load_news()[0], get_prices())


def term_for(day: date) -> tuple:
    return TERMS[(day - START_DATE).days % len(TERMS)]


@st.fragment(run_every="30m")  # re-checks the date so the term changes at midnight even on an open page
def terms_section() -> None:
    today = datetime.now(IST).date()
    term, cat, meaning, example = term_for(today)
    with st.container(border=True, key="card_term_of_day"):
        st.caption(f"📚 Term of the day · {today:%A, %d %B %Y}")
        st.markdown(f"## {md_safe(term)}")
        st.markdown(f":blue-badge[{cat}]")
        st.markdown(md_safe(meaning))
        st.markdown(f"*Example:* {md_safe(example)}")
    st.caption(f"A new term every day, in a fixed order, so nothing repeats for {len(TERMS)} days.")

    seen: Counter = Counter()
    for s in load_news()[0]:
        for name, mean in glossary_hits(f"{s['title']} {s['summary']}"):
            seen[(name, mean)] += 1
    if seen:
        st.subheader("📰 Terms in today's news")
        for (name, mean), n in seen.most_common(6):
            st.markdown(f"**{md_safe(name)}**: {md_safe(mean)} *(in {n} stor{'ies' if n != 1 else 'y'})*")

    past = [d for d in (today - timedelta(days=i) for i in range(1, 8)) if d >= START_DATE]
    if past:
        with st.expander("🗓️ Previous days"):
            for d in past:
                t, c, m, _ = term_for(d)
                st.markdown(f"**{d:%a %d %b} · {md_safe(t)}**: {md_safe(m)}")

    with st.expander("🔎 Browse all terms"):
        pick = st.pills("Category", ["All", "Investing", "Markets", "Economy", "Company"], selection_mode="single",
                        default="All", key="terms_cat", label_visibility="collapsed")
        q = st.text_input("Search terms", key="terms_q", placeholder="Search a term or its meaning", label_visibility="collapsed").strip().lower()
        rows = [{"Term": t, "Category": c, "Meaning": m, "Example": e} for t, c, m, e in TERMS
                if (pick in (None, "All") or c == pick) and (not q or q in f"{t} {m}".lower())]
        st.dataframe(pd.DataFrame(rows), hide_index=True, **PLOT_KW)


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
    t_news, t_movers, t_focus, t_terms = st.tabs(["📰 News", "📈 Gainers & losers", "🔥 Stocks in focus", "📚 Financial terms"])
    with t_news:
        news_section()
    with t_movers:
        movers_section()
    with t_focus:
        focus_section()
    with t_terms:
        terms_section()
    st.divider()
    st.caption(DISCLAIMER)
    st.caption(f"{ORG_NAME} {VERSION}")
    if FEEDBACK_URL:
        st.link_button("Found a problem? Tell us", FEEDBACK_URL)


main()
