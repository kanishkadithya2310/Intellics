"""Intellics: prices module (split out of app.py)."""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from companies import COMPANIES
import streamlit as st
import yfinance as yf

from config import INDICES, IST, PRICE_REFRESH, log


# -------------------------------------------------------------- price data
# yfinance threads=True starts one worker per ticker (about 145 now), which exceeds the thread limit on
# Streamlit Cloud. A small fixed number keeps the download fast without exhausting threads.
DOWNLOAD_THREADS = 4


def _fast_info(ticker: str):
    fi = yf.Ticker(ticker).fast_info
    last, prev = float(fi["last_price"]), float(fi["previous_close"])
    return ticker, (last, (last / prev - 1) * 100)


@st.cache_data(ttl=PRICE_REFRESH, show_spinner=False)
def load_prices(tickers: tuple[str, ...]) -> dict[str, tuple[float, float]]:
    out: dict = {}
    try:
        df = yf.download(list(tickers), period="7d", interval="1d", group_by="ticker",
                         progress=False, auto_adjust=False, threads=DOWNLOAD_THREADS)
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
        with ThreadPoolExecutor(max_workers=4) as pool:
            for res in pool.map(lambda t: _safe(_fast_info, t), missing):
                if res:
                    out[res[0]] = res[1]
    return out


def _safe(fn, arg):
    try:
        return fn(arg)
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


def market_label(ts: datetime | None) -> str:
    """Plain-words market status. Uses the time of the newest data point too, so a trading holiday
    (a weekday with no trading) is not wrongly described as 'open'."""
    now = datetime.now(IST)
    hm = (now.hour, now.minute)
    in_hours = now.weekday() < 5 and (9, 15) <= hm <= (15, 30)
    if not in_hours:
        return "Market closed: showing the last session"
    if ts is None:
        return "Market hours: freshness of the data could not be checked"
    if ts.astimezone(IST).date() == now.date():
        lag = (now - ts).total_seconds() / 60
        return "Market open" + (f" · data is about {lag:.0f} min behind" if lag > 2 else " (prices may be delayed)")
    if hm < (9, 45):
        return "Market just opened: waiting for today's first prices"
    return "No trading data for today (holiday?): showing the last session"


def market_dot(label: str) -> str:
    """Dot colour for the status pill: green while the market is open, amber otherwise."""
    return "g" if label.startswith("Market open") else "a"
