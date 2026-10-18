"""Intellics: markets module (split out of app.py)."""
from __future__ import annotations
import html

from companies import COMPANIES, SECTORS
import plotly.graph_objects as go
import streamlit as st

from company import company_explorer
from config import PLOT_KW, PRICE_REFRESH
from helpers import _stamp, md_safe, safe_url, small, time_ago
from news import load_news
from news_page import refresh_all
from prices import all_tickers, load_data_time, load_prices, market_dot, market_label, mover_rows
from ui import metrics_row, mood_bar


def sector_heatmap(rows: list) -> None:
    """Treemap of the tracked companies grouped by sector. Colour = today's % move (green up, red down)."""
    groups: dict[str, list[tuple[str, float]]] = {}
    for name, _, _, pct in rows:
        groups.setdefault(SECTORS.get(name, "Others"), []).append((name, pct))
    labels, parents, values, colors, texts = [], [], [], [], []
    for sector, items in groups.items():
        avg = sum(p for _, p in items) / len(items)
        labels.append(sector)
        parents.append("")
        values.append(0)
        colors.append(avg)
        texts.append(f"{avg:+.2f}% avg")
        for name, pct in items:
            labels.append(name)
            parents.append(sector)
            values.append(1)
            colors.append(pct)
            texts.append(f"{pct:+.2f}%")
    limit = max(2.0, max(abs(c) for c in colors))
    fig = go.Figure(go.Treemap(
        labels=labels, parents=parents, values=values, branchvalues="remainder", text=texts,
        texttemplate="%{label}<br>%{text}", hovertemplate="%{label}: %{text}<extra></extra>",
        marker=dict(colors=colors, cmin=-limit, cmax=limit, cmid=0, line=dict(width=1, color="#0a0f1f"),
                    colorscale=[[0, "#ef4444"], [0.5, "#334155"], [1, "#22c55e"]]),
        pathbar=dict(visible=False)))
    fig.update_layout(height=560, margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor="rgba(0,0,0,0)",
                      font_color="#f8fafc", dragmode=False)
    st.subheader("🗺️ Sector heatmap")
    st.plotly_chart(fig, **PLOT_KW, config={"displayModeBar": False})
    st.caption("Each box is one company, grouped by sector (our own simple grouping). Same size for every company; "
               "colour shows today's move vs previous close.")


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

    sector_heatmap(rows)
    company_explorer(rows, stories)


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
                meta = small(s["source"] + " · " + time_ago(s["ts"]))
                st.markdown(f"- [{md_safe(s['title'])}]({safe_url(s['link'])})  \n  {meta}", unsafe_allow_html=True)


def price_status() -> str:
    ts = load_data_time()
    if not ts:
        return market_label(None) + " · time of latest data unavailable"
    return f"Latest price data: {_stamp(ts)} · {market_label(ts)}"


@st.fragment(run_every=f"{PRICE_REFRESH}s")
def price_bar() -> None:
    prices = load_prices(all_tickers())
    label = market_label(load_data_time())
    st.markdown(f'<div class="market-status"><span class="gdot {market_dot(label)}"></span>{html.escape(label)}</div>', unsafe_allow_html=True)
    metrics_row(prices)
    st.caption(price_status() + f" · updates every {PRICE_REFRESH} sec")
    mood_bar(mover_rows(prices))


@st.fragment(run_every=f"{PRICE_REFRESH}s")
def movers_section() -> None:
    movers_tab(mover_rows(load_prices(all_tickers())), load_news()[0])
    st.caption(price_status())


@st.fragment(run_every="60s")
def focus_section() -> None:
    focus_tab(load_news()[0], load_prices(all_tickers()))
