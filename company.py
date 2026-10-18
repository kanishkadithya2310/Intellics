"""Intellics: company module (split out of app.py)."""
from __future__ import annotations
from datetime import datetime, timedelta
import html
import re
import textwrap
import time
import urllib.parse

import feedparser
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import streamlit as st
import yfinance as yf

from config import FAIL_PAUSE, IST, PLOT_KW, PRICE_REFRESH, log, trusted_publisher
from helpers import _stamp, _store, clean_text, md_safe, safe_url, small, time_ago
from news import http_get
from prices import market_label


# ------------------------------------------------------- company deep-dive
# Same range buttons as Google Finance
RANGES = {"1D": ("1d", "5m"), "5D": ("5d", "15m"), "1M": ("1mo", "1d"), "6M": ("6mo", "1d"),
          "YTD": ("ytd", "1d"), "1Y": ("1y", "1d"), "5Y": ("5y", "1wk"), "Max": ("max", "1mo")}


def _history(ticker: str, period: str, interval: str):
    df = yf.Ticker(ticker).history(period=period, interval=interval)[["Open", "High", "Low", "Close", "Volume"]]
    df = df.dropna(subset=["Open", "High", "Low", "Close"])
    df["Volume"] = df["Volume"].fillna(0)
    if len(df) < 2:
        raise ValueError("no price history")  # raising (instead of returning None) stops the failure being cached
    return df


@st.cache_data(ttl=60, show_spinner=False)
def _ohlc_intraday(ticker: str, period: str, interval: str):
    return _history(ticker, period, interval)


@st.cache_data(ttl=900, show_spinner=False)
def _ohlc_daily(ticker: str, period: str, interval: str):
    return _history(ticker, period, interval)


def load_ohlc(ticker: str, period: str, interval: str):
    """Intraday charts refresh every minute, daily/weekly/monthly ones every 15 minutes. Failures are never cached."""
    fn = _ohlc_daily if interval in ("1d", "1wk", "1mo") else _ohlc_intraday
    try:
        return fn(ticker, period, interval)
    except Exception as exc:
        log.warning("History failed for %s: %s", ticker, exc)
        return None


def last_point_time(ticker: str) -> datetime | None:
    """Time of the newest real price point for this company (IST), or None if it cannot be found."""
    df = load_ohlc(ticker, "1d", "5m")
    if df is None:
        return None
    ts = df.index[-1]
    ts = ts.tz_localize("UTC") if ts.tzinfo is None else ts
    return ts.tz_convert(IST).to_pydatetime()


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
        resp = http_get(url, timeout=8)
        for entry in feedparser.parse(resp.content).entries[:12]:
            title, publisher = clean_text(entry.get("title", "")), ""
            link = (entry.get("link") or "").strip()
            if " - " in title:
                title, publisher = title.rsplit(" - ", 1)
            if title and re.match(r"^https?://", link, re.I) and trusted_publisher(publisher):
                return {"title": title, "publisher": publisher.strip(), "link": link}
    except Exception as exc:
        log.warning("Move headline failed (%s, %s): %s", name, day, exc)
    return None


FUND_KEYS = ("trailingPE", "forwardPE", "priceToBook", "debtToEquity", "returnOnEquity", "profitMargins", "marketCap",
             "fiftyTwoWeekHigh", "fiftyTwoWeekLow", "dividendRate", "trailingEps", "bookValue", "sector", "industry",
             "longName")


RATIO_KEYS = ("priceToBook", "trailingEps", "returnOnEquity", "profitMargins", "debtToEquity", "bookValue")


@st.cache_data(ttl=3600, show_spinner=False)
def _load_info(ticker: str) -> dict:
    """Full company info from Yahoo (two attempts). Raises when Yahoo gives too little, so a failure is NOT cached for an hour."""
    last_exc: Exception = RuntimeError("no data")
    for attempt in (0, 1):
        try:
            info = yf.Ticker(ticker).get_info() or {}
            out = {k: info[k] for k in FUND_KEYS if info.get(k) is not None}
            if len(out) >= 3:
                return out
            last_exc = RuntimeError("Yahoo returned too little data")
        except Exception as exc:
            last_exc = exc
        if attempt == 0:
            time.sleep(0.6)
    raise last_exc


@st.cache_data(ttl=120, show_spinner=False)
def _load_fast_fund(ticker: str) -> dict:
    """Lighter backup numbers (market cap, 52-week range) that Yahoo rarely blocks."""
    out: dict = {}
    try:
        fi = yf.Ticker(ticker).fast_info
    except Exception:
        return out
    for key, fast_key in (("marketCap", "market_cap"), ("fiftyTwoWeekHigh", "year_high"), ("fiftyTwoWeekLow", "year_low")):
        try:
            v = float(fi[fast_key])
            if v == v:
                out[key] = v
        except Exception:
            pass
    return out


def load_fundamentals(ticker: str) -> dict:
    out: dict = {}
    fails = _store()["info_fail"]
    if time.time() - fails.get(ticker, 0) > FAIL_PAUSE:  # after a failure, leave Yahoo alone for a couple of minutes
        try:
            out = dict(_load_info(ticker))
        except Exception as exc:
            fails[ticker] = time.time()
            log.warning("Fundamentals failed for %s: %s", ticker, exc)
    for k, v in _load_fast_fund(ticker).items():
        out.setdefault(k, v)
    return out


def retry_fundamentals() -> None:
    _load_info.clear()
    _load_fast_fund.clear()
    _store()["info_fail"].clear()


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


@st.cache_data(ttl=6 * 3600, show_spinner=False)
def load_last_dividend(ticker: str):
    """The most recent dividend paid per share (None if the company has never paid one)."""
    try:
        d = yf.Ticker(ticker).dividends.dropna()
        if len(d):
            return float(d.iloc[-1])
    except Exception as exc:
        log.warning("Dividend lookup failed for %s: %s", ticker, exc)
    return None


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


def gf_grid(items: list[tuple[str, str]]) -> None:
    """Google Finance style details: three columns on a laptop (filled top to bottom), one column on a phone."""
    cells = "".join(f'<div class="gfr"><span class="k">{html.escape(k)}</span><span class="v">{html.escape(v)}</span></div>'
                    for k, v in items)
    st.markdown(f'<div class="gf">{cells}</div>', unsafe_allow_html=True)


def info_table(items: list[tuple]) -> None:
    """Clean two-column table: label on the left, value on the right. items = (label, value, tooltip)."""
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
        st.button("🔄 Try again", on_click=retry_fundamentals, key="retry_fund_all")
        return
    bars = (range_bar("Today's low", "Today's high", day.get("dayLow"), day.get("dayHigh"), price)
            + range_bar("52-week low", "52-week high", f.get("fiftyTwoWeekLow"), f.get("fiftyTwoWeekHigh"), price))
    if bars:
        st.markdown("**📈 Where is the price now?**")
        st.markdown(bars, unsafe_allow_html=True)

    de, roe, pm = f.get("debtToEquity"), f.get("returnOnEquity"), f.get("profitMargins")
    de = de / 100 if de is not None else None      # Yahoo gives debt/equity as a percentage
    roe = roe * 100 if roe is not None else None   # Yahoo gives ROE and margin as fractions (0.15 = 15%)
    pm = pm * 100 if pm is not None else None
    st.markdown("**📋 Fundamentals**")
    if not any(f.get(k) is not None for k in RATIO_KEYS):
        st.info("Yahoo Finance didn't send the company ratios (P/B, EPS, return on equity...) this time. "
                "This happens often with free data on cloud apps. A dash (—) means 'not available', not zero.")
        st.button("🔄 Try again", on_click=retry_fundamentals, key="retry_fund")
    info_table([
        ("P/B ratio", _num(f.get("priceToBook"), "x", 2),
         "Share price compared with the company's book value (assets minus debts) per share."),
        ("EPS (yearly)", _rs(f.get("trailingEps")), "Profit earned per share over the last year."),
        ("Book value", _rs(f.get("bookValue")), "The company's net worth (assets minus debts) per share."),
        ("Debt to equity", _num(de, "x", 2),
         "How much the company has borrowed for every Rs 1 of its own money. Lower usually means less risk. Not meaningful for banks."),
        ("Return on equity", _num(roe, "%"), "Profit earned on shareholders' money. Higher usually means the company uses money well."),
        ("Profit margin", _num(pm, "%"), "The share of sales the company keeps as profit."),
        ("Prev. close", _rs(day.get("prevClose")), "The price at which the share closed on the previous trading day."),
        ("Volume", _volume(day.get("volume")), "How many shares have changed hands today."),
    ])
    with st.expander("How to read these numbers"):
        st.markdown("- **P/E**: lower can mean cheaper, higher can mean investors expect growth. Compare within the same industry.\n"
                    "- **Debt to equity**: above 1 means more borrowed money than own money (normal for banks and finance firms).\n"
                    "- **Return on equity**: 15% or more is often seen as good.\n"
                    "- **Range bars**: the closer the dot is to the right, the closer the price is to its high.")
    st.caption("Numbers come from Yahoo Finance and can be missing or out of date. They are for learning, not advice to buy or sell.")


def _breaks(df, interval: str, intraday: bool) -> list[dict]:
    """Hide weekends, non-trading hours and market holidays so the chart has no empty gaps."""
    if interval in ("1wk", "1mo"):
        return []
    breaks = [dict(bounds=["sat", "mon"])]
    if intraday:
        breaks.append(dict(bounds=[15.5, 9.25], pattern="hour"))
    else:
        have = set(df.index.date)
        missing = [d.strftime("%Y-%m-%d") for d in pd.bdate_range(df.index[0].date(), df.index[-1].date()) if d.date() not in have]
        if missing:
            breaks.append(dict(values=missing))
    return breaks


def _rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


def build_chart(df, kind: str, intraday: bool, interval: str, moves: list, heads: dict,
                ref: float, ref_label: str, show_vol: bool, smas: set):
    """Google Finance look: soft green/red area that fades downward, dotted reference line, values on the left."""
    up = float(df["Close"].iloc[-1]) >= ref
    color = "#81c995" if up else "#f28b82"
    hi_s, lo_s = (df["High"], df["Low"]) if kind == "Candles" else (df["Close"], df["Close"])
    lo, hi = float(lo_s.min()), float(hi_s.max())
    pad = (max(hi, ref) - min(lo, ref)) * 0.12 or 1
    y0, y1 = min(lo, ref) - pad, max(hi, ref) + pad
    fig = make_subplots(rows=2 if show_vol else 1, cols=1, shared_xaxes=True, vertical_spacing=0.03,
                        row_heights=[0.8, 0.2] if show_vol else [1.0])
    if kind == "Candles":
        fig.add_trace(go.Candlestick(x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
                                     increasing_line_color="#22c55e", decreasing_line_color="#ef4444",
                                     name="Price", showlegend=False), row=1, col=1)
    else:
        base = dict(x=df.index, y=df["Close"], mode="lines", name="Price", showlegend=False,
                    line=dict(color=color, width=2), fill="tozeroy", fillcolor=_rgba(color, 0.14),
                    hovertemplate="%{y:,.2f} INR<extra></extra>")
        try:  # fade the colour from the line down to the bottom (needs a recent Plotly)
            trace = go.Scatter(**base, fillgradient=dict(type="vertical", start=y0, stop=hi, colorscale=[
                [0, _rgba(color, 0.0)], [1, _rgba(color, 0.40)]]))
        except (ValueError, TypeError):
            trace = go.Scatter(**base)
        fig.add_trace(trace, row=1, col=1)
    fig.add_hline(y=ref, line_dash="dot", line_color="rgba(203,213,225,.7)", line_width=1, row=1, col=1,
                  annotation_text=f"{ref_label}<br>{ref:,.2f}" if ref_label else None,
                  annotation_position="bottom right", annotation_font=dict(size=11, color="#cbd5e1"))
    for n, col in ((20, "#f59e0b"), (50, "#60a5fa")):
        if n in smas and len(df) > n:
            fig.add_trace(go.Scatter(x=df.index, y=df["Close"].rolling(n).mean(), mode="lines", name=f"SMA {n}",
                                     line=dict(color=col, width=1.4), hovertemplate=f"SMA {n}: %{{y:,.2f}}<extra></extra>"),
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
                                 marker=dict(size=12, symbol="diamond", line=dict(width=1.5, color="white"),
                                             color=["#22c55e" if m[2] > 0 else "#ef4444" for m in moves]),
                                 text=text, hovertemplate="%{text}<extra></extra>"), row=1, col=1)
    if show_vol:
        vcol = ["rgba(129,201,149,.55)" if c >= o else "rgba(242,139,130,.55)" for o, c in zip(df["Open"], df["Close"])]
        fig.add_trace(go.Bar(x=df.index, y=df["Volume"], marker_color=vcol, name="Volume", showlegend=False,
                             hovertemplate="Volume: %{y:,.0f}<extra></extra>"), row=2, col=1)
        fig.update_yaxes(showgrid=False, tickformat=".2s", row=2, col=1)
    span_days = (df.index[-1] - df.index[0]).days
    tick = "%I:%M %p" if intraday and span_days < 2 else "%d %b" if span_days <= 200 else "%b %Y"
    fig.update_xaxes(rangebreaks=_breaks(df, interval, intraday), rangeslider_visible=False, showgrid=False,
                     showspikes=True, spikemode="across", spikesnap="cursor", spikethickness=1, spikedash="dot",
                     spikecolor="#9aa0a6", tickformat=tick,
                     hoverformat="%d %b, %I:%M %p" if intraday else "%d %b %Y")
    fig.update_yaxes(range=[y0, y1], side="left", showgrid=True, gridcolor="rgba(255,255,255,.08)", zeroline=False,
                     tickformat=",.0f" if y1 >= 200 else ",.2f", row=1, col=1)
    fig.update_layout(height=430 if show_vol else 360, margin=dict(l=0, r=0, t=6, b=0), paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", font_color="#e8eaed", dragmode=False, hovermode="x unified",
                      hoverlabel=dict(bgcolor="#303134", font_color="#e8eaed"), showlegend=bool(smas),
                      legend=dict(orientation="h", y=1.05, x=0))
    return fig


def company_explorer(rows: list, stories: list[dict]) -> None:
    st.subheader("🔍 Explore a company")
    pick = st.selectbox("Search or pick a company", sorted([r[0] for r in rows]), key="explore")
    row = next(r for r in rows if r[0] == pick)
    ticker, price, day_pct = row[1], row[2], row[3]
    with st.spinner("Loading company numbers…"):
        fund, day, last_div = load_fundamentals(ticker), load_day_stats(ticker), load_last_dividend(ticker)
        point_time = last_point_time(ticker)

    # Google Finance style header: name, NSE code, big price, change badge and today's rupee change
    prev = price / (1 + day_pct / 100) if day_pct > -99 else price
    cls, arrow = ("up", "↑") if day_pct >= 0 else ("dn", "↓")
    when = f"Last data point: {_stamp(point_time)}" if point_time else "Time of last data point unavailable"
    st.markdown(f'<div class="gf-head"><div class="gf-title">{html.escape(fund.get("longName") or pick)}</div>'
                f'<div class="gf-sub">NSE: {html.escape(ticker.replace(".NS", ""))}'
                + (f' · {html.escape(fund["sector"])}' if fund.get("sector") else "") + '</div>'
                f'<div class="gf-row"><span><span class="gf-price">{price:,.2f}</span><span class="gf-cur">INR</span></span>'
                f'<span class="gf-badge {cls}">{arrow} {abs(day_pct):.2f}%</span>'
                f'<span class="gf-today {cls}">{price - prev:+,.2f} today</span></div>'
                f'<div class="gf-time">{html.escape(when)} · {html.escape(market_label(point_time))} · source: Yahoo Finance</div></div>',
                unsafe_allow_html=True)

    rng = st.pills("Time range", list(RANGES), selection_mode="single", default="1D", key="range",
                   label_visibility="collapsed") or "1D"
    kind = st.session_state.get("ctype") or "Line"      # chart options sit below the chart, so read their saved values
    ind = st.session_state.get("ind") or []
    period, interval = RANGES[rng]
    df = load_ohlc(ticker, period, interval)
    if df is None:
        st.info("Price history isn't available for this range right now. Try another range.")
    else:
        intraday = interval not in ("1d", "1wk", "1mo")
        moves = [] if (intraday or interval == "1mo") else big_moves(df, weekly=interval == "1wk")
        heads: dict = {}
        if moves:
            with st.spinner("Looking up why it moved…"):
                heads = {m[0]: move_headline(pick, m[0].strftime("%Y-%m-%d")) for m in moves}
        first, last = float(df["Close"].iloc[0]), float(df["Close"].iloc[-1])
        ref, ref_label = (prev, "Previous close") if rng == "1D" else (first, "")
        fig = build_chart(df, kind, intraday, interval, moves, heads, ref, ref_label, "Volume" in ind,
                          {int(i.split()[1]) for i in ind if i.startswith("SMA")})
        st.plotly_chart(fig, **PLOT_KW, config={"displayModeBar": False})
        # for 1D we reuse the header's previous close, so both percentages always agree
        r_chg = (price - prev) if rng == "1D" else last - first
        r_pct = day_pct if rng == "1D" else (last / first - 1) * 100
        c = "up" if r_chg >= 0 else "dn"
        st.markdown(f'<div class="gf-note">{html.escape(rng)} change: <b class="{c}">{"▲" if r_chg >= 0 else "▼"} '
                    f'{r_chg:+,.2f} ({r_pct:+.2f}%)</b> &nbsp;·&nbsp; High ₹{df["High"].max():,.2f} &nbsp;·&nbsp; '
                    f'Low ₹{df["Low"].min():,.2f}</div>', unsafe_allow_html=True)
    with st.expander("⚙️ Chart options"):
        a, b = st.columns(2)
        a.pills("Chart type", ["Line", "Candles"], selection_mode="single", default="Line", key="ctype")
        b.pills("Indicators", ["Volume", "SMA 20", "SMA 50"], selection_mode="multi", default=[], key="ind")

    # P/E: use Yahoo's number; if it is missing but yearly EPS is known, work it out as price / EPS
    pe, eps = fund.get("trailingPE"), fund.get("trailingEps")
    pe_label = "P/E ratio"
    if pe is None and eps and eps > 0:
        pe, pe_label = price / eps, "P/E (price ÷ EPS)"
    dy = fund["dividendRate"] / price * 100 if fund.get("dividendRate") and price else None
    gf_grid([("Open", _num(day.get("open"), "", 2)), ("High", _num(day.get("dayHigh"), "", 2)),
             ("Low", _num(day.get("dayLow"), "", 2)),
             ("Mkt cap", _crore(fund.get("marketCap"))), (pe_label, _num(pe, "", 2)),
             ("52-wk high", _num(fund.get("fiftyTwoWeekHigh"), "", 2)),
             ("Dividend yield", _num(dy, "%", 2)), ("Last dividend", _rs(last_div)),
             ("52-wk low", _num(fund.get("fiftyTwoWeekLow"), "", 2))])

    if df is not None and not intraday and moves:
        st.markdown("**⚡ Biggest moves and what was in the news**")
        for ts, _, pct in reversed(moves):
            head = heads.get(ts)
            label = f"{ts:%d %b %Y} · {'▲' if pct > 0 else '▼'} {pct:+.1f}%"
            if head:
                st.markdown(f"- **{label}**: [{md_safe(head['title'])}]({safe_url(head['link'])})  \n"
                            f"  {small(head['publisher'])}", unsafe_allow_html=True)
            else:
                st.markdown(f"- **{label}**: no matching headline found from a trusted publisher")
        st.caption("Diamonds on the chart mark these days. The headline is the top news result around that date, "
                   "so it may not be the real cause. Please open the article to check.")
    elif df is not None and not intraday and interval != "1mo":
        st.caption("No unusually big single moves in this range.")

    analysis_card(price, fund, day)

    related = [s for s in stories if pick in s["tags"]][:3]
    st.markdown("**Latest news on this company**" if related else "No recent headlines mention this company.")
    for s in related:
        meta = small(s["source"] + " · " + time_ago(s["ts"]))
        st.markdown(f"- [{md_safe(s['title'])}]({safe_url(s['link'])})  \n  {meta}", unsafe_allow_html=True)
