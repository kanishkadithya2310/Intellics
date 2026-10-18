"""Intellics Trading Challenge v1.7: a virtual stock-trading competition.

Everyone starts with Rs 10,00,000 of PLAY money and trades the companies tracked by the app at the latest
(possibly delayed) price. No real money is involved.

Rankings
- This week: % return since the last closed week (or since the player joined). Because it is a % return,
  somebody who joins late can still win the week. Top 3 get a title.
- This month: % return since the end of last month's final closed week. Top 3 get a title.
- Overall: total portfolio value. Never resets. Top 10 get a title.
- Weekly winners: the winner of every closed week.

v1.7
- The week closes BY ITSELF on Saturday (00:00 IST). app.py calls auto_close_if_due() on every visit; it does
  nothing on weekdays and never raises.
- The organiser panel is hidden from players. It only appears when the app is opened with the secret link
  (https://YOUR-APP.streamlit.app/?page=game&organiser=YOUR_ORGANISER_KEY) and it still needs the admin password to
  close a week.
- Database check button (organiser panel): tests the URL, the key, both tables and a real write.
- Works with the new Supabase keys (sb_secret_...) as well as the old service_role key.

Where the scores are kept
- Nothing to set up: PRACTICE MODE. Scores live in the app's memory and are lost whenever the app restarts.
- Permanent scores: run supabase_setup.sql in Supabase, then add the secrets SUPABASE_URL, SUPABASE_KEY (the SECRET key),
  ADMIN_PIN and ORGANISER_KEY. The game switches to the database automatically.

This file must sit next to app.py. app.py calls trading_game.game_tab(...) and trading_game.auto_close_if_due(...).
"""
from __future__ import annotations

import base64
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
from datetime import datetime, timedelta, timezone
from typing import Callable
from zoneinfo import ZoneInfo

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
MAX_PIN_TRIES = 5             # wrong PINs allowed before the account is locked
LOCK_MINUTES = 15             # how long a locked account stays locked (saved in the database)
MIN_WEEK_GAP_MINUTES = 30     # protects against closing the week twice by accident
MIN_PRICE_COVERAGE = 0.7      # at least this share of companies must have a price before a week can be closed
ADMIN_MAX_TRIES = 5           # wrong admin passwords allowed before the organiser panel pauses
ADMIN_LOCK_MINUTES = 15
WEEKS_SHOWN = 12              # closed weeks kept on screen
AUTO_CHECK_SECONDS = 300      # how often a weekend visit may re-check whether the week still needs closing
AUTO_GRACE_HOURS = 12         # a week closed by hand up to this long before Saturday 00:00 counts as "already closed"
WEEK_TOP, MONTH_TOP, OVERALL_TOP = 3, 3, 10   # how many players earn a title
IST = ZoneInfo("Asia/Kolkata")
PLOT_KW = {} if hasattr(st, "iframe") else {"use_container_width": True}  # new vs old Streamlit (same trick as app.py)

NICK_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _.-]{2,19}$")
PIN_RE = re.compile(r"^\d{6,8}$")
NAME_RE = re.compile(r"^[A-Za-z][A-Za-z .'\-]{1,39}$")
PUBLIC_COLUMNS = "nick_key,display,real_name,cash,holdings,start_nifty,created_at"
WEEK_TITLES = ["🥇 Week champion", "🥈 Week runner-up", "🥉 Week third"]
MONTH_TITLES = ["🥇 Month champion", "🥈 Month runner-up", "🥉 Month third"]


class GameDBError(Exception):
    """Something went wrong talking to the score database. The message is safe to show to players;
    `detail` (technical) is shown only in the organiser's database check."""

    def __init__(self, message: str, detail: str = ""):
        super().__init__(message)
        self.detail = detail


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


def _who(display: str, real: str | None) -> str:
    """HTML for a trader's name: the real name (if they chose to share it) with the nickname in brackets."""
    if real:
        return f'{_esc(real)} <span style="opacity:.65">({_esc(display)})</span>'
    return _esc(display)


def _who_plain(display: str, real: str | None) -> str:
    return f"{real} ({display})" if real else display


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat(timespec="seconds")


def _parse_ts(text) -> datetime | None:
    s = str(text).replace("Z", "+00:00")
    s = re.sub(r"\.(\d+)", lambda m: "." + m.group(1).ljust(6, "0")[:6], s)  # older Pythons need exactly 6 decimals
    try:
        dt = datetime.fromisoformat(s)
    except (TypeError, ValueError):
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


# ---------------------------------------------------------------- storage
@st.cache_resource
def _memory_db() -> dict:
    return {"players": {}, "weeks": [], "lock": threading.Lock(), "admin": {"fails": 0, "until": 0.0},
            "auto": {"t": 0.0}}


def _secret(name: str) -> str:
    """A secret as clean text (stray spaces and quote marks removed), or '' when it is not set."""
    try:
        value = str(st.secrets.get(name, "") or "")
    except Exception:
        return ""
    return value.strip().strip("\"'").strip()


def _sb_config() -> tuple[str, str] | None:
    url, key = _secret("SUPABASE_URL").rstrip("/"), _secret("SUPABASE_KEY")
    if url.endswith("/rest/v1"):
        url = url[: -len("/rest/v1")]
    return (url, key) if url.startswith("https://") and key else None


def _sb_secrets_present() -> bool:
    return bool(_secret("SUPABASE_URL") or _secret("SUPABASE_KEY"))


def db_mode() -> str:
    return "supabase" if _sb_config() else "practice"


def _key_problem(key: str) -> str:
    """Spots the PUBLIC key by mistake. The game needs the SECRET key, because the tables are locked to the public one."""
    if key.startswith("sb_publishable_"):
        return ("SUPABASE_KEY is the PUBLISHABLE (public) key. Use the SECRET key (starts with sb_secret_) "
                "or the legacy service_role key.")
    if key.count(".") == 2:  # an old-style key is a JWT: peek at its 'role'
        try:
            payload = key.split(".")[1]
            role = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4))).get("role")
            if role == "anon":
                return "SUPABASE_KEY is the anon (public) key. Use the service_role key or a secret key (sb_secret_...)."
        except Exception:
            pass
    return ""


def _sb(table: str, method: str, params: dict | None = None, body: dict | None = None) -> list:
    cfg = _sb_config()
    if not cfg:
        raise GameDBError("The score database is not set up.")
    url, key = cfg
    headers = {"apikey": key, "Content-Type": "application/json", "Prefer": "return=representation"}
    if not key.startswith("sb_"):  # the new sb_ keys are not JWTs and must only go in the apikey header
        headers["Authorization"] = f"Bearer {key}"
    try:
        resp = requests.request(method, f"{url}/rest/v1/{table}", headers=headers, params=params or {}, json=body, timeout=10)
    except requests.RequestException as exc:
        log.warning("Supabase unreachable: %s", exc)
        raise GameDBError("Could not reach the score database. Please try again in a moment.",
                          f"{type(exc).__name__}: check SUPABASE_URL and that the project is not paused") from exc
    if resp.status_code == 409:
        raise GameDBError("That nickname is already taken. Pick another." if table == "players"
                          else "That week has already been closed.")
    if resp.status_code >= 400:
        detail = f"HTTP {resp.status_code}: {resp.text[:200]}"
        log.warning("Supabase error on %s: %s", table, detail)  # never log the key
        if resp.status_code in (401, 403):
            hint = "The database rejected the key. The site owner should use the SECRET (service_role) key, not the public one."
        elif resp.status_code == 404 or "PGRST205" in resp.text or "42P01" in resp.text:
            hint = "The game tables were not found. The site owner should run supabase_setup.sql in Supabase."
        elif "42703" in resp.text or "PGRST204" in resp.text:
            hint = "A table column is missing. The site owner should run supabase_setup.sql again."
        else:
            hint = "The score database refused the request. The site owner should check the Supabase URL, key and tables."
        raise GameDBError(hint, detail)
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
    player["real_name"] = (player.get("real_name") or "").strip()
    player["pin_fails"] = int(player.get("pin_fails") or 0)
    return player


def db_get(nick_key: str) -> dict | None:
    if _sb_config():
        rows = _sb("players", "GET", {"season": f"eq.{SEASON}", "nick_key": f"eq.{nick_key}", "select": "*"})
        return _normalize(rows[0]) if rows else None
    mem = _memory_db()
    with mem["lock"]:
        found = mem["players"].get(nick_key)
        return _normalize(json.loads(json.dumps(found))) if found else None


def db_list() -> list[dict]:
    """Public columns of every player this season (never the PIN hash)."""
    if _sb_config():
        rows = _sb("players", "GET", {"season": f"eq.{SEASON}", "select": PUBLIC_COLUMNS, "limit": "1000"})
    else:
        mem = _memory_db()
        with mem["lock"]:
            rows = [{k: p.get(k) for k in PUBLIC_COLUMNS.split(",")} for p in mem["players"].values()]
    return [_normalize(r) for r in rows]


def db_insert(player: dict) -> None:
    if _sb_config():
        _sb("players", "POST", body=player)
        return
    mem = _memory_db()
    with mem["lock"]:
        if player["nick_key"] in mem["players"]:
            raise GameDBError("That nickname is already taken. Pick another.")
        if len(mem["players"]) >= MAX_PLAYERS_PRACTICE:
            raise GameDBError("Practice mode is full. Please try again later.")
        mem["players"][player["nick_key"]] = json.loads(json.dumps(player))


def db_patch(nick_key: str, fields: dict) -> None:
    if _sb_config():
        _sb("players", "PATCH", {"season": f"eq.{SEASON}", "nick_key": f"eq.{nick_key}"}, body=fields)
        return
    mem = _memory_db()
    with mem["lock"]:
        if nick_key in mem["players"]:
            mem["players"][nick_key].update(json.loads(json.dumps(fields)))


def db_save(player: dict) -> None:
    db_patch(player["nick_key"], {k: player[k] for k in ("cash", "holdings", "trades", "realized")})


def db_weeks(limit: int = WEEKS_SHOWN) -> list[dict]:
    """Closed weeks of this season, newest first."""
    if _sb_config():
        rows = _sb("game_weeks", "GET", {"season": f"eq.{SEASON}", "select": "*", "order": "week_no.desc", "limit": str(limit)})
    else:
        mem = _memory_db()
        with mem["lock"]:
            rows = json.loads(json.dumps(sorted(mem["weeks"], key=lambda w: w["week_no"], reverse=True)[:limit]))
    return rows


def db_insert_week(row: dict) -> None:
    if _sb_config():
        _sb("game_weeks", "POST", body=row)
        return
    mem = _memory_db()
    with mem["lock"]:
        if any(w["week_no"] == row["week_no"] for w in mem["weeks"]):
            raise GameDBError("That week has already been closed.")
        mem["weeks"].append(json.loads(json.dumps(row)))


@st.cache_data(ttl=20, show_spinner=False)
def _cached_list(mode: str) -> list[dict]:
    return db_list()


@st.cache_data(ttl=20, show_spinner=False)
def _cached_weeks(mode: str) -> list[dict]:
    return db_weeks()


def _clear_caches() -> None:
    _cached_list.clear()
    _cached_weeks.clear()


def db_check() -> list[tuple[bool, str]]:
    """Organiser tool: walks through everything the game needs and says what is wrong, in plain words."""
    cfg = _sb_config()
    if not cfg:
        why = ("SUPABASE_URL or SUPABASE_KEY is missing in the app's Secrets."
               if not _sb_secrets_present() else
               "SUPABASE_URL or SUPABASE_KEY is set but looks wrong (the URL must start with https:// and the key must not be empty).")
        return [(False, why + " The game is running in practice mode.")]
    url, key = cfg
    kind = "secret key" if key.startswith("sb_secret_") else "legacy JWT key" if key.count(".") == 2 else "key"
    out: list[tuple[bool, str]] = [(True, f"Found SUPABASE_URL ({url}) and a {kind}.")]
    problem = _key_problem(key)
    if problem:
        out.append((False, problem))
    for table in ("players", "game_weeks"):
        try:
            rows = _sb(table, "GET", {"season": f"eq.{SEASON}", "select": "*", "limit": "1000"})
            out.append((True, f"Table '{table}' is reachable ({len(rows)} row(s) in {SEASON})."))
        except GameDBError as exc:
            out.append((False, f"Table '{table}': {exc} [{exc.detail}]"))
    test_filter = {"season": f"eq.{SEASON}", "nick_key": "eq.__dbcheck__"}
    try:  # a real write: add one temporary row, then remove it (this is what a publishable key cannot do)
        _sb("players", "DELETE", test_filter)
        _sb("players", "POST", body={"season": SEASON, "nick_key": "__dbcheck__", "display": "dbcheck",
                                      "salt": "00", "pin_hash": "x"})
        _sb("players", "DELETE", test_filter)
        out.append((True, "Write test passed (one temporary test row was added and removed)."))
    except GameDBError as exc:
        out.append((False, f"Write test failed: {exc} [{exc.detail}]"))
        try:
            _sb("players", "DELETE", test_filter)
        except GameDBError:
            pass
    return out


# ----------------------------------------------------------- accounts (nickname + PIN)
def _hash_pin(pin: str, salt_hex: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", pin.encode(), bytes.fromhex(salt_hex), 150_000).hex()


def _weak_pin(pin: str) -> bool:
    """Repeated digits (111111) or a plain run (123456, 654321)."""
    if len(set(pin)) == 1:
        return True
    digits = [int(c) for c in pin]
    return {digits[i + 1] - digits[i] for i in range(len(digits) - 1)} in ({1}, {-1})


def clean_real_name(raw: str) -> tuple[str, str]:
    """Returns (cleaned name, error). An empty name is fine: it means 'show my nickname only'."""
    name = re.sub(r"\s+", " ", (raw or "").strip())
    if not name:
        return "", ""
    if not NAME_RE.match(name):
        return "", "Real name should be 2 to 40 letters (spaces, dots, hyphens allowed), or leave it empty."
    return name, ""


def register(nickname: str, pin: str, nifty_price: float | None, real_name: str = "") -> tuple[dict | None, str]:
    display = re.sub(r"\s+", " ", nickname.strip())
    if not NICK_RE.match(display):
        return None, "Nickname must be 3 to 20 characters: letters, numbers, spaces, dot, dash or underscore."
    if not PIN_RE.match(pin):
        return None, "PIN must be 6 to 8 digits."
    if _weak_pin(pin):
        return None, "That PIN is too easy to guess. Avoid repeated digits (like 111111) and simple runs (like 123456)."
    name, err = clean_real_name(real_name)
    if err:
        return None, err
    key = display.lower()
    if db_get(key):
        return None, "That nickname is already taken. Pick another."
    salt = secrets.token_hex(16)
    player = {"season": SEASON, "nick_key": key, "display": display, "real_name": name or None, "salt": salt,
              "pin_hash": _hash_pin(pin, salt), "cash": START_CASH, "holdings": {}, "trades": [], "realized": 0.0,
              "start_nifty": nifty_price, "created_at": _iso(_now())}
    db_insert(player)
    return _normalize(player), ""


def _lock_remaining(player: dict) -> float:
    until = _parse_ts(player.get("lock_until")) if player.get("lock_until") else None
    return max(0.0, (until - _now()).total_seconds()) if until else 0.0


def login(nickname: str, pin: str) -> tuple[dict | None, str]:
    """The wrong-PIN counter and the lock are saved in the database, so refreshing the page does not clear them."""
    key = re.sub(r"\s+", " ", nickname.strip()).lower()
    player = db_get(key) if key else None
    if player:
        left = _lock_remaining(player)
        if left > 0:
            return None, f"Too many wrong tries. This account is locked for about {math.ceil(left / 60)} more minute(s)."
    salt = (player or {}).get("salt") or "00" * 16
    ok = hmac.compare_digest(_hash_pin(pin, salt), (player or {}).get("pin_hash", "x"))
    if not player:
        return None, "Wrong nickname or PIN."
    if not ok:
        fails = player.get("pin_fails", 0) + 1
        patch: dict = {"pin_fails": fails}
        message = "Wrong nickname or PIN."
        if fails >= MAX_PIN_TRIES:
            patch = {"pin_fails": 0, "lock_until": _iso(_now() + timedelta(minutes=LOCK_MINUTES))}
            message = f"Too many wrong tries. This account is locked for {LOCK_MINUTES} minutes."
        try:
            db_patch(key, patch)
        except GameDBError:
            pass  # a failed counter update must never let the login through, and it never does
        return None, message
    if player.get("pin_fails") or player.get("lock_until"):
        try:
            db_patch(key, {"pin_fails": 0, "lock_until": None})
        except GameDBError:
            pass
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

    player["trades"].append({"t": _iso(_now()), "side": side, "ticker": ticker, "name": name, "qty": qty,
                             "price": round(price, 2)})
    del player["trades"][:-TRADE_LOG_LIMIT]
    return True, message


def week_bases(weeks: list[dict]) -> dict[str, float]:
    """Each player's value at the last 'Close week'. Anyone not in that list joined later and starts from START_CASH."""
    if not weeks:
        return {}
    return {r["key"]: float(r["end"]) for r in (weeks[0].get("results") or []) if r.get("key")}


def _month_start(now_ist: datetime | None = None) -> datetime:
    now_ist = now_ist or datetime.now(IST)
    return now_ist.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def month_bases(weeks: list[dict], now_ist: datetime | None = None) -> dict[str, float]:
    """Each player's value at the end of last month: the newest week closed BEFORE this month started.
    Players who are not in it (or if no week was closed before this month) start from START_CASH."""
    start = _month_start(now_ist)
    for w in weeks:  # newest first
        closed = _parse_ts(w.get("closed_at"))
        if closed and closed.astimezone(IST) < start:
            return {r["key"]: float(r["end"]) for r in (w.get("results") or []) if r.get("key")}
    return {}


def is_active(player: dict) -> bool:
    """Has this player done anything? Only active players can earn titles (so an empty account never 'wins')."""
    return bool(player["holdings"]) or abs(player["cash"] - START_CASH) > 0.005


def build_board(players: list[dict], price_of: dict[str, float], nifty_now: float | None,
                base_of: dict[str, float] | None = None, month_base_of: dict[str, float] | None = None) -> list[dict]:
    base_of, month_base_of = base_of or {}, month_base_of or {}
    rows = []
    for p in players:
        total, _, no_price = portfolio_value(p, price_of)
        ret = (total / START_CASH - 1) * 100
        beat = None
        if nifty_now and p.get("start_nifty"):
            beat = ret - (nifty_now / p["start_nifty"] - 1) * 100
        base = base_of.get(p["nick_key"], START_CASH)
        mbase = month_base_of.get(p["nick_key"], START_CASH)
        rows.append({"key": p["nick_key"], "name": p["display"], "real": p.get("real_name") or "", "total": total,
                     "ret": ret, "beat": beat, "positions": len(p["holdings"]), "no_price": no_price,
                     "base": base, "week_ret": (total / base - 1) * 100 if base > 0 else 0.0,
                     "month_ret": (total / mbase - 1) * 100 if mbase > 0 else 0.0, "active": is_active(p)})
    return rows


def award_titles(board: list[dict]) -> dict[str, dict[str, str]]:
    """{'week': {player key: title}, 'month': {...}, 'overall': {...}}. Only active players can earn one."""
    act = [r for r in board if r["active"]]
    week = sorted(act, key=lambda r: (r["week_ret"], r["total"]), reverse=True)[:WEEK_TOP]
    month = sorted(act, key=lambda r: (r["month_ret"], r["total"]), reverse=True)[:MONTH_TOP]
    overall = sorted(act, key=lambda r: r["total"], reverse=True)[:OVERALL_TOP]
    overall_label = lambda i: "👑 Overall champion" if i == 0 else "💎 Overall top 3" if i < 3 else "⭐ Overall top 10"
    return {"week": {r["key"]: WEEK_TITLES[i] for i, r in enumerate(week)},
            "month": {r["key"]: MONTH_TITLES[i] for i, r in enumerate(month)},
            "overall": {r["key"]: overall_label(i) for i, r in enumerate(overall)}}


def titles_of(titles: dict[str, dict[str, str]], key: str) -> list[str]:
    return [titles[c][key] for c in ("overall", "month", "week") if key in titles[c]]


def compute_week(players: list[dict], price_of: dict[str, float], base_of: dict[str, float]) -> list[dict]:
    """Final result of one week for every player, best first. Ties go to the higher portfolio value."""
    results = []
    for r in build_board(players, price_of, None, base_of):
        results.append({"key": r["key"], "name": r["name"], "real": r["real"], "start": round(r["base"], 2),
                        "end": round(r["total"], 2), "ret": round(r["week_ret"], 4)})
    results.sort(key=lambda r: (r["ret"], r["end"]), reverse=True)
    return results


def close_week(prices: dict, tracked_tickers: list[str]) -> tuple[bool, str]:
    """Saves the winner and everyone's closing value (the next week's starting point).
    Used by the organiser button AND by the automatic Saturday close."""
    price_of = {t: v[0] for t, v in prices.items() if v and v[0]}
    tracked = list(tracked_tickers)
    if not tracked or sum(1 for t in tracked if t in price_of) < MIN_PRICE_COVERAGE * len(tracked):
        return False, "Prices did not load properly, so the week was NOT closed. Wait a minute and try again."
    try:
        players = db_list()
        if not players:
            return False, "There are no players yet, so there is nothing to close."
        weeks = db_weeks(1)
        last = weeks[0] if weeks else None
        if last:
            closed = _parse_ts(last.get("closed_at"))
            if closed and _now() - closed < timedelta(minutes=MIN_WEEK_GAP_MINUTES):
                return False, (f"Week {last['week_no']} was closed less than {MIN_WEEK_GAP_MINUTES} minutes ago, "
                               "so this looks like a double click. Nothing was changed.")
        missing = sorted({t for p in players for t in p["holdings"] if t not in price_of})
        if missing:
            return False, (f"No price for {len(missing)} share(s) that players hold ({', '.join(missing[:3])}"
                           f"{'...' if len(missing) > 3 else ''}). The week was NOT closed. Try again in a minute.")
        results = compute_week(players, price_of, week_bases(weeks))
        week_no = int(last["week_no"]) + 1 if last else 1
        win = results[0]
        db_insert_week({"season": SEASON, "week_no": week_no, "closed_at": _iso(_now()), "winner_key": win["key"],
                        "winner_name": win["name"], "winner_ret": win["ret"], "results": results})
    except GameDBError as exc:
        return False, str(exc)
    _clear_caches()
    return True, f"Week {week_no} closed. Winner: {_who_plain(win['name'], win['real'])} with {_pct(win['ret'])}."


def _saturday_start(now_ist: datetime) -> datetime:
    """00:00 IST of the Saturday that began the current weekend (call it only on a Saturday or Sunday)."""
    return (now_ist - timedelta(days=(now_ist.weekday() - 5) % 7)).replace(hour=0, minute=0, second=0, microsecond=0)


def auto_close_if_due(get_prices: Callable[[], dict], tracked_tickers: list[str] | None = None) -> None:
    """Closes the week by itself once Saturday 00:00 IST has passed. app.py calls this on every visit.
    - Weekdays: returns at once (no database call, no price download).
    - Weekends: checks at most every few minutes; closes only if this weekend's close has not happened yet.
    - Never raises. If prices or the database are unavailable it simply tries again a few minutes later.
    Two visitors at the same moment cannot close the week twice (the database refuses a duplicate week)."""
    try:
        now = datetime.now(IST)
        if now.weekday() < 5:
            return
        auto = _memory_db()["auto"]
        if time.time() - auto["t"] < AUTO_CHECK_SECONDS:
            return
        auto["t"] = time.time()
        last = db_weeks(1)
        if last:
            closed = _parse_ts(last[0].get("closed_at"))
            if closed and closed >= _saturday_start(now) - timedelta(hours=AUTO_GRACE_HOURS):
                return  # already closed for this weekend
        if not db_list():
            return
        ok, message = close_week(get_prices() or {}, list(tracked_tickers or []))
        log.info("Auto-close: %s", message)
    except Exception as exc:  # never let the game take the whole app down
        log.warning("Auto-close skipped: %s", exc)


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


def _day(ts_text) -> str:
    ts = _parse_ts(ts_text)
    return f"{ts.astimezone(IST):%d %b %Y}" if ts else "-"


# ------------------------------------------------------------------ pieces of the page
def _mode_banner() -> None:
    if db_mode() == "practice":
        if _sb_secrets_present():
            st.warning("The database secrets are set but look wrong (the URL must start with https:// and the key must not be empty), "
                       "so the game is running in practice mode and scores will NOT be saved.")
        else:
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
            try:
                player, err = login(nick, pin)
            except GameDBError as exc:
                player, err = None, str(exc)
            if player:
                ss.update(g_nick=player["nick_key"], g_player=player)
                st.rerun()
            st.error(err)
    with join_tab:
        st.write(f"Start with **{_inr(START_CASH)}** of play money and see how you rank against everyone else.")
        with st.form("g_join_form"):
            nick = st.text_input("Choose a nickname (shown publicly)", key="g_join_nick", max_chars=20,
                                 help="3 to 20 characters. Please do not use anyone else's name.")
            real = st.text_input("Your real name (optional)", key="g_join_real", max_chars=40,
                                 help="Leave this empty to appear only by your nickname. If you fill it in, "
                                      "your name will be shown publicly on the leaderboard.")
            st.caption("Optional: add your real name only if you want it published on the leaderboard.")
            pin = st.text_input("Choose a PIN (6 to 8 digits)", type="password", key="g_join_pin", max_chars=8,
                                help="You need it to log back in. It is stored scrambled, but do not reuse a PIN from anywhere else.")
            go_join = st.form_submit_button("Start trading", type="primary")
        if go_join:
            try:
                player, err = register(nick, pin, nifty_price, real)
            except GameDBError as exc:
                player, err = None, str(exc)
            if player:
                _clear_caches()
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
    _clear_caches()
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


def _name_panel(player: dict) -> None:
    """Lets a player add, change or remove the real name shown next to their nickname."""
    st.caption("Your nickname is always shown. If you add your real name, it is shown publicly next to it. "
               "Empty the box and save to show only your nickname.")
    with st.form("g_name_form"):
        new = st.text_input("Real name", value=player.get("real_name") or "", key="g_real_edit", max_chars=40)
        save = st.form_submit_button("Save name")
    if save:
        name, err = clean_real_name(new)
        if err:
            st.error(err)
            return
        try:
            db_patch(player["nick_key"], {"real_name": name or None})
        except GameDBError as exc:
            st.error(str(exc))
            return
        player["real_name"] = name
        st.session_state["g_player"] = player
        _clear_caches()
        st.session_state["g_flash"] = "Name saved." if name else "Name removed. Only your nickname is shown."
        st.rerun()


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


def _next_close_text(now_ist: datetime | None = None) -> str:
    now_ist = now_ist or datetime.now(IST)
    days = (5 - now_ist.weekday()) % 7
    nxt = (now_ist + timedelta(days=days)).replace(hour=0, minute=0, second=0, microsecond=0)
    if nxt <= now_ist:
        nxt += timedelta(days=7)
    return f"{nxt:%A, %d %b} at 12:00 am IST"


def _week_tab(board: list[dict], weeks: list[dict], me: str | None, titles: dict) -> None:
    week_no = (int(weeks[0]["week_no"]) if weeks else 0) + 1
    since = f"since {_day(weeks[0].get('closed_at'))}" if weeks else "since each player joined"
    st.markdown(f"**Week {week_no}** · % return {since}")
    ranked = sorted(board, key=lambda r: (r["week_ret"], r["total"]), reverse=True)
    medals = {0: "🥇", 1: "🥈", 2: "🥉"}
    rows, me_row = [], None
    for i, r in enumerate(ranked[:BOARD_SIZE]):
        if r["key"] == me:
            me_row = i
        rows.append([medals.get(i, str(i + 1)), _who(r["name"], r["real"]),
                     f'<span class="{_cls(r["week_ret"])}">{_pct(r["week_ret"])}</span>', _inr(r["total"]),
                     _esc(titles["week"].get(r["key"], ""))])
    _table([("#", False), ("Trader", False), ("This week", True), ("Portfolio value", True), ("Title", False)], rows, me_row)
    mine = next((i for i, r in enumerate(ranked) if r["key"] == me), None) if me else None
    if mine is not None and me_row is None:
        st.caption(f"Your rank this week: #{mine + 1} of {len(ranked)} ({_pct(ranked[mine]['week_ret'])})")
    st.caption(f"Ranked by % return, so joining late does not hurt you. The week closes by itself on {_next_close_text()}. "
               f"Top {WEEK_TOP} earn a title (players who have not traded yet cannot).")


def _month_tab(board: list[dict], me: str | None, titles: dict) -> None:
    st.markdown(f"**{datetime.now(IST):%B %Y}** · % return since the end of last month")
    ranked = sorted(board, key=lambda r: (r["month_ret"], r["total"]), reverse=True)
    medals = {0: "🥇", 1: "🥈", 2: "🥉"}
    rows, me_row = [], None
    for i, r in enumerate(ranked[:BOARD_SIZE]):
        if r["key"] == me:
            me_row = i
        rows.append([medals.get(i, str(i + 1)), _who(r["name"], r["real"]),
                     f'<span class="{_cls(r["month_ret"])}">{_pct(r["month_ret"])}</span>', _inr(r["total"]),
                     _esc(titles["month"].get(r["key"], ""))])
    _table([("#", False), ("Trader", False), ("This month", True), ("Portfolio value", True), ("Title", False)], rows, me_row)
    mine = next((i for i, r in enumerate(ranked) if r["key"] == me), None) if me else None
    if mine is not None and me_row is None:
        st.caption(f"Your rank this month: #{mine + 1} of {len(ranked)} ({_pct(ranked[mine]['month_ret'])})")
    st.caption(f"The month starts from each player's value when the last week of the previous month was closed "
               f"(or from the day they joined). Top {MONTH_TOP} earn a title.")


def _overall_tab(board: list[dict], me: str | None, titles: dict) -> None:
    ranked = sorted(board, key=lambda r: r["total"], reverse=True)
    medals = {0: "🥇", 1: "🥈", 2: "🥉"}
    rows, me_row = [], None
    for i, r in enumerate(ranked[:BOARD_SIZE]):
        if r["key"] == me:
            me_row = i
        beat = "-" if r["beat"] is None else f'<span class="{_cls(r["beat"])}">{_pct(r["beat"])}</span>'
        rows.append([medals.get(i, str(i + 1)), _who(r["name"], r["real"]), _inr(r["total"]),
                     f'<span class="{_cls(r["ret"])}">{_pct(r["ret"])}</span>', beat,
                     _esc(titles["overall"].get(r["key"], ""))])
    _table([("#", False), ("Trader", False), ("Portfolio value", True), ("Return", True), ("vs Nifty 50", True), ("Title", False)],
           rows, me_row)
    mine = next((i for i, r in enumerate(ranked) if r["key"] == me), None) if me else None
    if mine is not None and me_row is None:
        st.caption(f"Your overall rank: #{mine + 1} of {len(ranked)} ({_inr(ranked[mine]['total'])})")
    st.caption(f"Ranked by total portfolio value. Never resets. Top {OVERALL_TOP} earn a title. "
               "'vs Nifty 50' compares your return with the Nifty since you joined.")


def _winners_tab(weeks: list[dict]) -> None:
    if not weeks:
        st.info("No week has been closed yet. The first winner will appear here.")
        return
    rows = []
    for w in weeks:
        res = w.get("results") or []
        top = res[0] if res else {"name": w.get("winner_name", "-"), "real": "", "ret": w.get("winner_ret") or 0.0}
        rows.append([f"Week {w['week_no']}", _day(w.get("closed_at")), _who(top["name"], top.get("real")),
                     f'<span class="{_cls(top["ret"])}">{_pct(top["ret"])}</span>', str(len(res))])
    _table([("Week", False), ("Closed on", False), ("Winner", False), ("Return", True), ("Players", True)], rows)
    for w in weeks[:5]:
        res = (w.get("results") or [])[:5]
        if not res:
            continue
        with st.expander(f"Week {w['week_no']}: top {len(res)}"):
            _table([("#", False), ("Trader", False), ("Return", True), ("Value at close", True)],
                   [[str(i + 1), _who(r["name"], r.get("real")), f'<span class="{_cls(r["ret"])}">{_pct(r["ret"])}</span>',
                     _inr(r["end"])] for i, r in enumerate(res)])


@st.fragment(run_every=f"{BOARD_REFRESH}s")
def leaderboard_section(get_prices: Callable[[], dict], nifty_ticker: str, me: str | None) -> None:
    prices = get_prices()
    price_of = {t: v[0] for t, v in prices.items()}
    try:
        players = _cached_list(db_mode())
        weeks = _cached_weeks(db_mode())
    except GameDBError as exc:
        st.warning(str(exc))
        return
    st.subheader("🏅 Leaderboard")
    if not players:
        st.info("No traders yet. Be the first to join!")
        return
    board = build_board(players, price_of, price_of.get(nifty_ticker), week_bases(weeks), month_bases(weeks))
    titles = award_titles(board)
    week_tab, month_tab, overall_tab, winners_tab = st.tabs(["This week", "This month", "Overall", "Weekly winners"])
    with week_tab:
        _week_tab(board, weeks, me, titles)
    with month_tab:
        _month_tab(board, me, titles)
    with overall_tab:
        _overall_tab(board, me, titles)
    with winners_tab:
        _winners_tab(weeks)
    st.caption(f"{len(board)} trader(s) this season · refreshes about every {BOARD_REFRESH} sec")


# ------------------------------------------------------------------ organiser (hidden)
def _organiser_link() -> bool:
    """True only when the page was opened with ?organiser=<ORGANISER_KEY>. Players never see the panel."""
    key = _secret("ORGANISER_KEY")
    if not key:
        return False
    try:
        given = str(st.query_params.get("organiser") or "")
    except Exception:
        return False
    return bool(given) and hmac.compare_digest(given.encode(), key.encode())


def _organiser_panel(get_prices: Callable[[], dict], companies: dict[str, str]) -> None:
    if not _organiser_link():
        return
    with st.expander("🔐 Organisers only", expanded=True):
        if st.session_state.get("g_admin_msg"):
            ok, text = st.session_state.pop("g_admin_msg")
            (st.success if ok else st.error)(text)

        st.markdown("**1. Database check**")
        if st.button("Check the database", key="g_dbcheck_btn"):
            with st.spinner("Checking…"):
                results = db_check()
            for ok, text in results:
                (st.success if ok else st.error)(text)
            if all(ok for ok, _ in results):
                st.success("Everything looks good. Scores are being saved permanently.")

        st.markdown("**2. Close the week**")
        secret = _secret("ADMIN_PIN")
        if not secret:
            st.info("The admin password is not set. Add ADMIN_PIN in the app's Secrets to use this button.")
            return
        st.caption("The week already closes by itself on Saturday at 12:00 am IST. Use this only to close it early by hand. "
                   "It saves everyone's value as next week's starting point and announces the winner. It cannot be undone from the app.")
        password = st.text_input("Admin password", type="password", key="g_admin_pw")
        sure = st.checkbox("I am sure I want to close this week", key="g_admin_sure")
        if not st.button("Close week now", type="primary", key="g_close_btn"):
            return
        admin = _memory_db()["admin"]
        if time.time() < admin["until"]:
            st.error(f"Too many wrong passwords. Try again in about {int((admin['until'] - time.time()) // 60) + 1} minute(s).")
        elif not hmac.compare_digest(password.encode(), secret.encode()):
            admin["fails"] += 1
            if admin["fails"] >= ADMIN_MAX_TRIES:
                admin["fails"], admin["until"] = 0, time.time() + ADMIN_LOCK_MINUTES * 60
            st.error("Wrong password.")
        elif not sure:
            st.warning("Tick the box to confirm.")
        else:
            admin["fails"] = 0
            st.session_state["g_admin_msg"] = close_week(get_prices(), list(companies.values()))
            st.rerun()


def _rules_panel() -> None:
    st.markdown(f"""**How it works**

- Everyone starts with **{_inr(START_CASH)}** of play money. No real money is ever used.
- Buy and sell whole shares of the companies tracked on Intellics, at the latest price the free data source has.
  That price can be delayed, so it may differ from the real market.
- **Weekly ranking:** your % return for the week. The week closes **by itself every Saturday at 12:00 am IST**, and the best
  return wins. Because it is a percentage, joining late does not stop you from winning a week. Your first week counts from the day you join.
- **Monthly ranking:** your % return since the end of last month.
- **Overall ranking:** total portfolio value (cash plus the current value of your shares). It never resets.
- **Titles:** top {WEEK_TOP} each week, top {MONTH_TOP} each month and top {OVERALL_TOP} overall. You must have made at least one trade to earn a title.
- A player who holds only cash scores 0% for the week, so can win a week when the market falls. That is allowed.
- No short selling, no borrowing, and no brokerage fees or taxes.
- **Diversify:** when you buy, one company may be at most **{MAX_POSITION_PCT:.0f}%** of your portfolio.
- One account per person, please. Pick a nickname that is fine to show publicly.

**Your data**

We store your nickname, a scrambled version of your PIN, and your trades. Your real name is stored and shown **only if you choose
to add it**, and you can remove it any time from My name. No email address is collected.
Your PIN has 6 to 8 digits. After {MAX_PIN_TRIES} wrong tries the account locks for {LOCK_MINUTES} minutes. There is no PIN reset, so remember it.

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
        _organiser_panel(get_prices, companies)
        with st.expander("Rules"):
            _rules_panel()
        return

    weeks: list[dict] = []
    try:
        weeks = _cached_weeks(db_mode())
    except GameDBError:
        pass
    base = week_bases(weeks).get(player["nick_key"], START_CASH)
    total, _, no_price = portfolio_value(player, price_of)
    ret = (total / START_CASH - 1) * 100
    left, right = st.columns([3, 1])
    left.markdown(f"**Trader: {_md_safe(_who_plain(player['display'], player.get('real_name')))}**")
    right.button("Log out", on_click=_clear_login, key="g_logout")
    tiles = [("Portfolio value", _inr(total), ret), ("This week", _pct((total / base - 1) * 100), None),
             ("Cash", _inr(player["cash"]), None), ("Realised profit", _inr(player.get("realized", 0.0)), None)]
    if nifty_now and player.get("start_nifty"):
        tiles.append(("Nifty 50 since you joined", _pct((nifty_now / player["start_nifty"] - 1) * 100), None))
    _tiles(tiles)
    if no_price:
        st.caption(f"{no_price} holding(s) have no live price right now and are valued at your purchase price.")
    try:  # your titles, if any
        board = build_board(_cached_list(db_mode()), price_of, nifty_now, week_bases(weeks), month_bases(weeks))
        mine = titles_of(award_titles(board), player["nick_key"])
        if mine:
            st.success("Your titles right now: " + " · ".join(mine))
    except GameDBError:
        pass

    trade_tab, folio_tab, board_tab, name_tab, rules_tab = st.tabs(
        ["📈 Trade", "💼 My portfolio", "🏅 Leaderboard", "👤 My name", "📜 Rules"])
    with trade_tab:
        _trade_panel(player, companies, prices, price_of)
    with folio_tab:
        _portfolio_panel(player, price_of)
    with board_tab:
        leaderboard_section(get_prices, nifty_ticker, player["nick_key"])
        _organiser_panel(get_prices, companies)
    with name_tab:
        st.markdown("#### Leaderboard name (optional)")
        _name_panel(player)
    with rules_tab:
        _rules_panel()
