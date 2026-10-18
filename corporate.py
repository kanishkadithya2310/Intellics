"""Intellics: corporate module (split out of app.py)."""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta
import time

from companies import COMPANIES
import requests
import streamlit as st
import yfinance as yf

from config import IST, log
from helpers import _store, clean_text, md_safe


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
        a.button("🔄 Try again", on_click=retry_nse, key="ca_retry")
        if b.button("Show dividends from a backup source", key="ca_backup"):
            st.session_state["ca_use_backup"] = True
        st.link_button("Open the official NSE page ↗", NSE_PAGE)
        if st.session_state.get("ca_use_backup"):
            with st.spinner("Checking the large companies (this can take up to a minute)…"):
                actions = load_dividend_backup()
            source = "Yahoo Finance (dividends of the large companies tracked here)"
            if not actions:
                st.info("The backup source found no upcoming dividends right now.")
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
def _fetch_nse_actions() -> list[dict]:
    """Upcoming dividends, splits and bonus issues from the NSE (next 45 days). Raises on failure (so it is not cached)."""
    today = datetime.now(IST).date()
    url = ("https://www.nseindia.com/api/corporates-corporateActions?index=equities"
           f"&from_date={today:%d-%m-%Y}&to_date={today + timedelta(days=45):%d-%m-%Y}")
    session = requests.Session()
    session.headers.update(NSE_HEADERS)
    session.get("https://www.nseindia.com", timeout=6)  # NSE needs this first to hand out cookies
    resp = session.get(url, timeout=10)
    resp.raise_for_status()
    out: list[dict] = []
    for item in resp.json():
        subject = clean_text(item.get("subject", ""))
        kind, ex = _action_kind(subject), _nse_date(item.get("exDate"))
        if kind and ex and ex >= today:
            out.append({"company": item.get("comp") or item.get("symbol") or "?", "symbol": item.get("symbol", ""),
                        "kind": kind, "detail": subject, "ex": ex, "record": _nse_date(item.get("recDate"))})
    if not out:
        raise ValueError("NSE returned no usable rows")
    return sorted(out, key=lambda a: (a["ex"], a["company"]))


def load_corporate_actions() -> list[dict]:
    """NSE list, or [] if NSE is blocking us. After a failure we pause a few minutes instead of hammering NSE on every visit."""
    fails = _store()["nse_fail"]
    if time.time() - fails.get("t", 0) < 300:
        return []
    try:
        return _fetch_nse_actions()
    except Exception as exc:
        fails["t"] = time.time()
        log.warning("NSE corporate actions failed: %s", exc)
        return []


def retry_nse() -> None:
    _fetch_nse_actions.clear()
    _store()["nse_fail"].clear()
