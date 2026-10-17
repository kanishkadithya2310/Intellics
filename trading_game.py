"""Intellics Trading Challenge: a virtual stock-trading competition.

Everyone starts with Rs 10,00,000 of PLAY money and trades the companies tracked by the app at the latest
(possibly delayed) price. A shared leaderboard ranks everybody. No real money is involved.

Where the scores are kept
- Nothing to set up: the game runs in PRACTICE MODE. Scores live in the app's memory and are lost whenever the
  app restarts or goes to sleep. Fine for a demo.
- Permanent scores: connect a free Supabase database (see SUPABASE_SQL below and the two secrets
  SUPABASE_URL and SUPABASE_KEY). The game switches to it automatically.

This file must sit next to app.py. app.py calls trading_game.game_tab(...).
"""
from __future__ import annotations

import hashlib
import hmac
import html
import json
import logging
import math
import re
import secrets
import threading
import time
from datetime import datetime, timezone
from typing import Callable

import plotly.graph_objects as go
import requests
import streamlit as st

log = logging.getLogger("intellics.game")

# ------------------------------------------------------------------ settings
START_CASH = 1_000_000.0      # Rs 10 lakh of play money
SEASON = "season-1"           # change to "season-2" to start a brand-new competition (old scores stay in the database)
TRADING_OPEN = True           # set to False to close the competition (then take a screenshot of the leaderboard)
MAX_POSITION_PCT = 30.0       # one company may not be more than this % of your portfolio when you buy (100 = no limit)
BOARD_SIZE = 25               # rows shown on the leaderboard
BOARD_REFRESH = 60            # seconds between automatic leaderboard refreshes
TRADE_LOG_LIMIT = 300         # trades remembered per player
MAX_PLAYERS_PRACTICE = 500    # safety cap in practice mode
MAX_PIN_TRIES = 5             # wrong PINs allowed per visit before a short wait
LOCK_SECONDS = 60
PLOT_KW = {} if hasattr(st, "iframe") else {"use_container_width": True}  # new vs old Streamlit (same trick as app.py)

SUPABASE_SQL = """
create table if not exists players (
  season      text not null,
  nick_key    text not null,
  display     text not null,
  salt        text not null,
  pin_hash    text not null,
  cash        numeric not null,
  holdings    jsonb not null default '{}'::jsonb,
  trades      jsonb not null default '[]'::jsonb,
  realized    numeric not null default 0,
  start_nifty numeric,
  created_at  timestamptz not null default now(),
  primary key (season, nick_key)
);
alter table players enable row level security;  -- nobody can read it with the public key; only your secret key can
"""

NICK_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _.-]{2,19}$")
PIN_RE = re.compile(r"^\d{4,8}$")
PUBLIC_COLUMNS = "nick_key,display,cash,holdings,start_nifty,created_at"


class GameDBError(Exception):
    """Something went wrong talking to the score database. The message is safe to show to players."""


# ----------------------------------------------------------------- formatting
def _inr(x: float, decimals: int = 0) -> str:
    """Indian digit grouping: 1000000 -> Rs 10,00,000."""
    neg, x = x < 0, abs(x)
    whole, _, frac = f"{x:.{decimals}f}".partition(".")
    if len(whole) > 3:
        head, tail, groups = whole[:-3], whole[-3:], []
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        if head:
            groups.insert(0, head)
        whole = ",".join(groups + [tail])
    return f"{'-' if neg else ''}\u20b9{whole}" + (f".{frac}" if frac else "")


def _pct(x: float) -> str:
    return f"{x:+.2f}%"


def _cls(x: float) -> str:
    return "up" if x >= 0 else "dn"


def _esc(text) -> str:
    return html.escape(str(text), quote=True)


def _md_safe(text: str) -> str:
    return re.sub(r"([\\`*_\[\]$~#<>|])", r"\\\1", text)


# ---------------------------------------------------------------- storage
@st.cache_resource
def _memory_db() -> dict:
    return {"players": {}, "lock": threading.Lock()}


def _sb_config() -> tuple[str, str] | None:
    try:
        url = str(st.secrets.get("SUPABASE_URL", "") or "").rstrip("/")
        key = str(st.secrets.get("SUPABASE_KEY", "") or "")
    except Exception:
        return None
    return (url, key) if url.startswith("https://") and key else None


def db_mode() -> str:
    return "supabase" if _sb_config() else "practice"


def _sb(method: str, params: dict, body: dict | None = None) -> list:
    cfg = _sb_config()
    if not cfg:
        raise GameDBError("The score database is not set up.")
    url, key = cfg
    headers = {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json",
               "Prefer": "return=representation"}
    try:
        resp = requests.request(method, f"{url}/rest/v1/players", headers=headers, params=params, json=body, timeout=10)
    except requests.RequestException as exc:
        log.warning("Supabase unreachable: %s", exc)
        raise GameDBError("Could not reach the score database. Please try again in a moment.") from exc
    if resp.status_code == 409:
        raise GameDBError("That nickname is already taken. Pick another.")
    if resp.status_code >= 400:
        log.warning("Supabase error %s: %s", resp.status_code, resp.text[:200])  # never log the key
        raise GameDBError("The score database refused the request. The site owner should check the Supabase URL, key and table.")
    try:
        return resp.json() if resp.text else []
    except ValueError:
        return []


def _normalize(player: dict) -> dict:
    """Make sure numbers are real numbers and containers are real containers, whatever the database returned."""
    player["cash"] = float(player.get("cash") or 0)
    player["realized"] = float(player.get("realized") or 0)
    holdings = player.get("holdings") or {}
    player["holdings"] = {t: {"name": h.get("name", t), "qty": int(h.get("qty", 0)), "avg": float(h.get("avg", 0))}
                          for t, h in holdings.items() if int(h.get("qty", 0)) > 0}
    player["trades"] = list(player.get("trades") or [])
    start = player.get("start_nifty")
    player["start_nifty"] = float(start) if start else None
    return player


def db_get(nick_key: str) -> dict | None:
    if _sb_config():
        rows = _sb("GET", {"season": f"eq.{SEASON}", "nick_key": f"eq.{nick_key}", "select": "*"})
        return _normalize(rows[0]) if rows else None
    mem = _memory_db()
    with mem["lock"]:
        found = mem["players"].get(nick_key)
        return _normalize(json.loads(json.dumps(found))) if found else None


def db_list() -> list[dict]:
    """Public columns of every player this season (never the PIN hash)."""
    if _sb_config():
        rows = _sb("GET", {"season": f"eq.{SEASON}", "select": PUBLIC_COLUMNS, "limit": "1000"})
    else:
        mem = _memory_db()
        with mem["lock"]:
            rows = [{k: p.get(k) for k in PUBLIC_COLUMNS.split(",")} for p in mem["players"].values()]
    return [_normalize(r) for r in rows]


def db_insert(player: dict) -> None:
    if _sb_config():
        _sb("POST", {}, body=player)
        return
    mem = _memory_db()
    with mem["lock"]:
        if player["nick_key"] in mem["players"]:
            raise GameDBError("That nickname is already taken. Pick another.")
        if len(mem["players"]) >= MAX_PLAYERS_PRACTICE:
            raise GameDBError("Practice mode is full. Please try again later.")
        mem["players"][player["nick_key"]] = json.loads(json.dumps(player))


def db_save(player: dict) -> None:
    body = {k: player[k] for k in ("cash", "holdings", "trades", "realized")}
    if _sb_config():
        _sb("PATCH", {"season": f"eq.{SEASON}", "nick_key": f"eq.{player['nick_key']}"}, body=body)
        return
    mem = _memory_db()
    with mem["lock"]:
        if player["nick_key"] in mem["players"]:
            mem["players"][player["nick_key"]].update(json.loads(json.dumps(body)))


@st.cache_data(ttl=20, show_spinner=False)
def _cached_list(mode: str) -> list[dict]:
    return db_list()


# ----------------------------------------------------------- accounts (nickname + PIN)
def _hash_pin(pin: str, salt_hex: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", pin.encode(), bytes.fromhex(salt_hex), 150_000).hex()


def register(nickname: str, pin: str, nifty_price: float | None) -> tuple[dict | None, str]:
    display = re.sub(r"\s+", " ", nickname.strip())
    if not NICK_RE.match(display):
        return None, "Nickname must be 3 to 20 characters: letters, numbers, spaces, dot, dash or underscore."
    if not PIN_RE.match(pin):
        return None, "PIN must be 4 to 8 digits."
    key = display.lower()
    if db_get(key):
        return None, "That nickname is already taken. Pick another."
    salt = secrets.token_hex(16)
    player = {"season": SEASON, "nick_key": key, "display": display, "salt": salt, "pin_hash": _hash_pin(pin, salt),
              "cash": START_CASH, "holdings": {}, "trades": [], "realized": 0.0,
              "start_nifty": nifty_price, "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    db_insert(player)
    return _normalize(player), ""


def login(nickname: str, pin: str) -> tuple[dict | None, str]:
    key = re.sub(r"\s+", " ", nickname.strip()).lower()
    player = db_get(key) if key else None
    salt = (player or {}).get("salt") or "00" * 16
    ok = hmac.compare_digest(_hash_pin(pin, salt), (player or {}).get("pin_hash", "x"))
    if not player or not ok:
        return None, "Wrong nickname or PIN."
    return player, ""


# -------------------------------------------------------------- game rules (pure functions)
def portfolio_value(player: dict, price_of: dict[str, float]) -> tuple[float, float, int]:
    """Returns (total value, value of shares, number of holdings with no live price).
    A holding with no live price is valued at what you paid, so it never suddenly drops to zero."""
    shares, no_price = 0.0, 0
    for ticker, h in player["holdings"].items():
        price = price_of.get(ticker)
        if not price:
            price, no_price = h["avg"], no_price + 1
        shares += h["qty"] * price
    return player["cash"] + shares, shares, no_price


def execute_trade(player: dict, ticker: str, name: str, side: str, qty: int, price: float,
                  price_of: dict[str, float], max_pct: float = MAX_POSITION_PCT) -> tuple[bool, str]:
    """Apply one order to `player` (changed in place). Returns (success, message for the player)."""
    if not TRADING_OPEN:
        return False, "Trading is closed for this season."
    if not isinstance(qty, int) or qty < 1:
        return False, "Enter a whole number of shares (1 or more)."
    if not price or price <= 0 or not math.isfinite(price):
        return False, "There is no usable price for this company right now. Try again in a minute."
    holdings = player["holdings"]
    held = holdings.get(ticker)
    have = held["qty"] if held else 0

    if side == "Buy":
        cost = round(qty * price, 2)
        if cost > player["cash"] + 1e-6:
            return False, f"Not enough cash for {qty:,} shares ({_inr(cost, 2)}). You can afford up to {int(player['cash'] // price):,}."
        if max_pct < 100:
            total, _, _ = portfolio_value(player, price_of)
            limit_value = total * max_pct / 100
            if (have + qty) * price > limit_value + 1e-6:
                room = int(max(0.0, limit_value - have * price) // price)
                return False, (f"Diversify! One company can be at most {max_pct:.0f}% of your portfolio "
                               f"({_inr(limit_value)} right now). You can add up to {room:,} more share(s) of {name}.")
        new_qty = have + qty
        avg = ((held["avg"] * have if held else 0.0) + cost) / new_qty
        holdings[ticker] = {"name": name, "qty": new_qty, "avg": round(avg, 4)}
        player["cash"] = round(player["cash"] - cost, 2)
        message = f"Bought {qty:,} {name} at {_inr(price, 2)} for {_inr(cost, 2)}."
    elif side == "Sell":
        if have < qty:
            return False, f"You only hold {have:,} share(s) of {name}."
        proceeds = round(qty * price, 2)
        player["realized"] = round(player.get("realized", 0.0) + (price - held["avg"]) * qty, 2)
        player["cash"] = round(player["cash"] + proceeds, 2)
        if have == qty:
            del holdings[ticker]
        else:
            held["qty"] = have - qty
        message = f"Sold {qty:,} {name} at {_inr(price, 2)} for {_inr(proceeds, 2)}."
    else:
        return False, "Choose Buy or Sell."

    player["trades"].append({"t": datetime.now(timezone.utc).isoformat(timespec="seconds"), "side": side,
                             "ticker": ticker, "name": name, "qty": qty, "price": round(price, 2)})
    del player["trades"][:-TRADE_LOG_LIMIT]
    return True, message


def build_board(players: list[dict], price_of: dict[str, float], nifty_now: float | None) -> list[dict]:
    rows = []
    for p in players:
        total, _, no_price = portfolio_value(p, price_of)
        ret = (total / START_CASH - 1) * 100
        beat = None
        if nifty_now and p.get("start_nifty"):
            beat = ret - (nifty_now / p["start_nifty"] - 1) * 100
        rows.append({"key": p["nick_key"], "name": p["display"], "total": total, "ret": ret, "beat": beat,
                     "positions": len(p["holdings"]), "no_price": no_price})
    rows.sort(key=lambda r: r["total"], reverse=True)
    return rows


# ----------------------------------------------------------------- display helpers
def _css() -> None:
    st.markdown("""<style>
.tg-wrap{overflow-x:auto;margin:.3rem 0 .8rem}
.tg{width:100%;border-collapse:collapse;font-size:.92rem}
.tg th{text-align:left;font-weight:500;opacity:.75;padding:8px 8px;border-bottom:1px solid rgba(255,255,255,.14);white-space:nowrap}
.tg td{padding:9px 8px;border-bottom:1px solid rgba(255,255,255,.07);white-space:nowrap}
.tg th.r,.tg td.r{text-align:right}
.tg tr.me td{background:rgba(96,165,250,.16)}
.tg .up{color:#4ade80}.tg .dn{color:#f87171}
</style>""", unsafe_allow_html=True)


def _table(headers: list[tuple[str, bool]], rows: list[list[str]], me_row: int | None = None) -> None:
    """headers = (label, right_aligned). Cells are trusted HTML that the caller has already escaped."""
    head = "".join(f'<th class="{"r" if right else ""}">{_esc(label)}</th>' for label, right in headers)
    body = ""
    for i, cells in enumerate(rows):
        tds = "".join(f'<td class="{"r" if headers[j][1] else ""}">{cell}</td>' for j, cell in enumerate(cells))
        body += f'<tr class="{"me" if i == me_row else ""}">{tds}</tr>'
    st.markdown(f'<div class="tg-wrap"><table class="tg"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>',
                unsafe_allow_html=True)


def _tiles(items: list[tuple[str, str, float | None]]) -> None:
    """Uses the .stat-grid / .stat styles that app.py already defines."""
    cells = ""
    for label, value, delta in items:
        extra = f'<div class="d {_cls(delta)}">{"&#9650;" if delta >= 0 else "&#9660;"} {_pct(delta)}</div>' if delta is not None else ""
        cells += f'<div class="stat"><div class="l">{_esc(label)}</div><div class="v">{_esc(value)}</div>{extra}</div>'
    st.markdown(f'<div class="stat-grid">{cells}</div>', unsafe_allow_html=True)


def _clear_login() -> None:
    for key in ("g_nick", "g_player"):
        st.session_state.pop(key, None)


# ------------------------------------------------------------------ pieces of the page
def _mode_banner() -> None:
    if db_mode() == "practice":
        st.info("**Practice mode.** Scores are kept only while the app is running and are cleared when it restarts or sleeps. "
                "The site owner can make them permanent by connecting a free Supabase database.")


def _auth_panel(nifty_price: float | None) -> None:
    ss = st.session_state
    login_tab, join_tab = st.tabs(["Log in", "Join the challenge"])
    with login_tab:
        with st.form("g_login_form"):
            nick = st.text_input("Nickname", key="g_login_nick", max_chars=20)
            pin = st.text_input("PIN", type="password", key="g_login_pin", max_chars=8)
            go_login = st.form_submit_button("Log in", type="primary")
        if go_login:
            if time.time() < ss.get("g_lock_until", 0):
                st.error(f"Too many wrong tries. Please wait about {int(ss['g_lock_until'] - time.time()) + 1} seconds.")
            else:
                try:
                    player, err = login(nick, pin)
                except GameDBError as exc:
                    player, err = None, str(exc)
                if player:
                    ss.update(g_nick=player["nick_key"], g_player=player, g_fails=0)
                    st.rerun()
                ss["g_fails"] = ss.get("g_fails", 0) + 1
                if ss["g_fails"] >= MAX_PIN_TRIES:
                    ss["g_lock_until"], ss["g_fails"] = time.time() + LOCK_SECONDS, 0
                st.error(err)
    with join_tab:
        st.write(f"Start with **{_inr(START_CASH)}** of play money and see how you rank against everyone else.")
        with st.form("g_join_form"):
            nick = st.text_input("Choose a nickname (shown publicly)", key="g_join_nick", max_chars=20,
                                 help="3 to 20 characters. Please do not use anyone else's name.")
            pin = st.text_input("Choose a PIN (4 to 8 digits)", type="password", key="g_join_pin", max_chars=8,
                                help="You need it to log back in. It is stored scrambled, but do not reuse a PIN from anywhere else.")
            go_join = st.form_submit_button("Start trading", type="primary")
        if go_join:
            try:
                player, err = register(nick, pin, nifty_price)
            except GameDBError as exc:
                player, err = None, str(exc)
            if player:
                _cached_list.clear()
                ss.update(g_nick=player["nick_key"], g_player=player,
                          g_flash=f"Welcome, {player['display']}! You have {_inr(START_CASH)} to invest.")
                st.rerun()
            st.error(err)


def _place_order(player: dict, ticker: str, name: str, side: str, qty: int, price: float, price_of: dict) -> None:
    try:
        fresh = db_get(player["nick_key"])  # use the newest saved copy, in case you also play on another device
        if not fresh:
            st.error("Your account could not be found. Please log in again.")
            return
        ok, message = execute_trade(fresh, ticker, name, side, int(qty), price, price_of)
        if not ok:
            st.error(message)
            return
        db_save(fresh)
    except GameDBError as exc:
        st.error(str(exc))
        return
    _cached_list.clear()
    st.session_state["g_player"] = fresh
    st.session_state["g_flash"] = message
    st.rerun()


def _trade_panel(player: dict, companies: dict[str, str], prices: dict, price_of: dict) -> None:
    if not TRADING_OPEN:
        st.warning("Trading is closed for this season. Check the leaderboard for the final standings.")
    options = sorted(n for n, t in companies.items() if t in prices)
    if not options:
        st.info("Prices are not available right now. Please try again in a minute.")
        return
    name = st.selectbox("Company", options, index=None, placeholder="Search a company...", key="g_company")
    if not name:
        st.caption(f"{len(options)} companies available. Prices come from a free source and can be delayed.")
        return
    ticker = companies[name]
    price, day_pct = prices[ticker]
    held = player["holdings"].get(ticker)
    colour = "green" if day_pct >= 0 else "red"
    st.markdown(f"**{_md_safe(name)}** &nbsp; {_inr(price, 2)} &nbsp; :{colour}[{_pct(day_pct)} today]")
    if held:
        gain = (price / held["avg"] - 1) * 100 if held["avg"] else 0.0
        st.caption(f"You hold {held['qty']:,} shares bought at an average of {_inr(held['avg'], 2)} ({_pct(gain)}).")
    side = st.radio("Order type", ["Buy", "Sell"], horizontal=True, key="g_side")
    if side == "Buy":
        st.caption(f"Cash available: {_inr(player['cash'], 2)}. You can afford up to {int(player['cash'] // price):,} shares.")
    qty = st.number_input("Number of shares", min_value=1, max_value=1_000_000, value=1, step=1, key="g_qty")
    st.write(f"Order value: **{_inr(qty * price, 2)}**")
    if st.button(f"Place {side.lower()} order", type="primary", key="g_place", disabled=not TRADING_OPEN):
        _place_order(player, ticker, name, side, qty, price, price_of)


def _portfolio_panel(player: dict, price_of: dict) -> None:
    holdings = player["holdings"]
    if not holdings:
        st.info("You have not bought anything yet. Open the Trade tab to place your first order.")
    else:
        rows, labels, values = [], [], []
        for ticker, h in sorted(holdings.items(), key=lambda kv: kv[1]["name"].lower()):
            price = price_of.get(ticker)
            shown = price or h["avg"]
            value = h["qty"] * shown
            gain = (shown / h["avg"] - 1) * 100 if h["avg"] else 0.0
            note = "" if price else " *"
            rows.append([_esc(h["name"]), f"{h['qty']:,}", _inr(h["avg"], 2), _inr(shown, 2) + note, _inr(value),
                         f'<span class="{_cls(gain)}">{_pct(gain)}</span>'])
            labels.append(h["name"])
            values.append(value)
        _table([("Company", False), ("Shares", True), ("Avg cost", True), ("Price", True), ("Value", True), ("Gain", True)], rows)
        if any(not price_of.get(t) for t in holdings):
            st.caption("* No live price right now, so this holding is shown at the price you paid.")
        if player["cash"] > 0:
            labels.append("Cash")
            values.append(player["cash"])
        fig = go.Figure(go.Pie(labels=labels, values=values, hole=0.55, sort=True, textinfo="label+percent",
                               hovertemplate="%{label}: %{value:,.0f}<extra></extra>"))
        fig.update_layout(height=340, margin=dict(l=0, r=0, t=10, b=0), paper_bgcolor="rgba(0,0,0,0)",
                          font_color="#e5e7eb", showlegend=False)
        st.markdown("**Where your money is**")
        st.plotly_chart(fig, **PLOT_KW, config={"displayModeBar": False})
    with st.expander(f"Trade history ({len(player['trades'])})"):
        trades = list(reversed(player["trades"]))[:50]
        if not trades:
            st.write("No trades yet.")
        else:
            _table([("When (UTC)", False), ("Type", False), ("Company", False), ("Shares", True), ("Price", True)],
                   [[_esc(t["t"].replace("T", " ")[:16]), _esc(t["side"]), _esc(t["name"]), f"{t['qty']:,}", _inr(t["price"], 2)]
                    for t in trades])


@st.fragment(run_every=f"{BOARD_REFRESH}s")
def leaderboard_section(get_prices: Callable[[], dict], nifty_ticker: str, me: str | None) -> None:
    prices = get_prices()
    price_of = {t: v[0] for t, v in prices.items()}
    try:
        players = _cached_list(db_mode())
    except GameDBError as exc:
        st.warning(str(exc))
        return
    board = build_board(players, price_of, price_of.get(nifty_ticker))
    st.subheader("🏅 Leaderboard")
    if not board:
        st.info("No traders yet. Be the first to join!")
        return
    medals = {0: "🥇", 1: "🥈", 2: "🥉"}
    rows, me_row = [], None
    for i, r in enumerate(board[:BOARD_SIZE]):
        if r["key"] == me:
            me_row = i
        beat = "-" if r["beat"] is None else f'<span class="{_cls(r["beat"])}">{_pct(r["beat"])}</span>'
        rows.append([medals.get(i, str(i + 1)), _esc(r["name"]), _inr(r["total"]),
                     f'<span class="{_cls(r["ret"])}">{_pct(r["ret"])}</span>', beat, str(r["positions"])])
    _table([("#", False), ("Trader", False), ("Portfolio value", True), ("Return", True), ("vs Nifty 50", True), ("Stocks", True)],
           rows, me_row)
    if me and me_row is None:
        mine = next((i for i, r in enumerate(board) if r["key"] == me), None)
        if mine is not None:
            st.caption(f"Your rank: #{mine + 1} of {len(board)} ({_inr(board[mine]['total'])})")
    st.caption(f"{len(board)} trader(s) this season · ranked by total portfolio value · refreshes about every {BOARD_REFRESH} sec. "
               "'vs Nifty 50' compares your return with the Nifty since you joined.")


def _rules_panel() -> None:
    st.markdown(f"""**How it works**

- Everyone starts with **{_inr(START_CASH)}** of play money. No real money is ever used.
- Buy and sell whole shares of the companies tracked on Intellics, at the latest price the free data source has.
  That price can be delayed, so it may differ from the real market.
- The leaderboard ranks everyone by **total portfolio value** (cash plus the current value of your shares).
- No short selling, no borrowing, and no brokerage fees or taxes.
- **Diversify:** when you buy, one company may be at most **{MAX_POSITION_PCT:.0f}%** of your portfolio.
- One account per person, please. Pick a nickname that is fine to show publicly.

**Your data**

We store only your nickname, a scrambled version of your PIN, and your trades. No email, no real name.
There is no PIN reset, so remember it.

**Important**

This is a learning game. Doing well here does not mean you would do well with real money, and nothing here is investment advice.""")


# ------------------------------------------------------------------ entry point
def game_tab(companies: dict[str, str], get_prices: Callable[[], dict], nifty_ticker: str) -> None:
    """companies: display name -> Yahoo ticker. get_prices(): {ticker: (price, % change today)}."""
    ss = st.session_state
    _css()
    st.subheader("🏆 Intellics Trading Challenge")
    st.caption(f"{SEASON.replace('-', ' ').title()} · {_inr(START_CASH)} of play money · no real money involved")
    _mode_banner()

    prices = get_prices()
    price_of = {t: v[0] for t, v in prices.items()}
    nifty_now = price_of.get(nifty_ticker)
    if ss.get("g_flash"):
        st.success(ss.pop("g_flash"))

    player = ss.get("g_player") if ss.get("g_nick") else None
    if not player:
        _auth_panel(nifty_now)
        leaderboard_section(get_prices, nifty_ticker, None)
        with st.expander("Rules"):
            _rules_panel()
        return

    total, _, no_price = portfolio_value(player, price_of)
    ret = (total / START_CASH - 1) * 100
    left, right = st.columns([3, 1])
    left.markdown(f"**Trader: {_md_safe(player['display'])}**")
    right.button("Log out", on_click=_clear_login, key="g_logout")
    tiles = [("Portfolio value", _inr(total), ret), ("Cash", _inr(player["cash"]), None),
             ("Realised profit", _inr(player.get("realized", 0.0)), None)]
    if nifty_now and player.get("start_nifty"):
        tiles.append(("Nifty 50 since you joined", _pct((nifty_now / player["start_nifty"] - 1) * 100), None))
    _tiles(tiles)
    if no_price:
        st.caption(f"{no_price} holding(s) have no live price right now and are valued at your purchase price.")

    trade_tab, folio_tab, board_tab, rules_tab = st.tabs(["📈 Trade", "💼 My portfolio", "🏅 Leaderboard", "📜 Rules"])
    with trade_tab:
        _trade_panel(player, companies, prices, price_of)
    with folio_tab:
        _portfolio_panel(player, price_of)
    with board_tab:
        leaderboard_section(get_prices, nifty_ticker, player["nick_key"])
    with rules_tab:
        _rules_panel()
