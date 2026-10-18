"""Intellics: ui module (split out of app.py)."""
from __future__ import annotations
import base64
import html
from functools import lru_cache

import streamlit as st

from config import BACKGROUND_IMAGE_URL, INDICES, LOGO_PATH, ORG_NAME, ORG_SUBTITLE, TAGLINE, VIDEO_URL


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
.block-container{{padding-top:3.2rem;max-width:1180px;position:relative;z-index:1}}
div[class*="st-key-card_"]{{background:rgba(255,255,255,.05);backdrop-filter:blur(10px);border:1px solid rgba(255,255,255,.1);
 border-radius:18px;padding:.4rem .6rem;transition:transform .2s,border-color .2s}}
div[class*="st-key-card_"]:hover{{transform:translateY(-3px);border-color:rgba(120,160,255,.6)}}
.hero-title{{font-size:2rem;font-weight:800;letter-spacing:.12em;line-height:1.15;margin:0}}
.brand{{position:relative;overflow:hidden;display:flex;align-items:center;gap:16px;margin:0 0 1.15rem;padding:1.15rem 1.3rem;background:linear-gradient(120deg,rgba(28,45,82,.82),rgba(45,26,76,.68));border:1px solid rgba(184,205,255,.18);border-radius:22px;box-shadow:0 18px 55px rgba(0,0,0,.22)}}
.brand::after{{content:"";position:absolute;width:240px;height:240px;right:-90px;top:-150px;border-radius:50%;background:rgba(115,126,255,.18);filter:blur(4px);pointer-events:none}}
.brand > *{{position:relative;z-index:1}}
.hero-eyebrow{{display:inline-flex;align-items:center;gap:7px;font-size:.68rem;font-weight:700;letter-spacing:.13em;color:#c7d2fe;margin-bottom:.34rem}}
.hero-eyebrow::before{{content:"";width:7px;height:7px;border-radius:50%;background:#5eead4;box-shadow:0 0 12px #5eead4}}
.hero-sub{{opacity:.85;margin-bottom:.6rem}}
.gdot{{--c:#4ade80;display:inline-block;width:8px;height:8px;flex:none;border-radius:50%;margin-right:7px;vertical-align:middle;background:var(--c);box-shadow:0 0 10px var(--c);animation:glow 2.4s ease-out infinite}}
.gdot.g{{--c:#4ade80}}.gdot.r{{--c:#f87171}}.gdot.a{{--c:#fbbf24}}
@keyframes glow{{0%{{box-shadow:0 0 0 0 color-mix(in srgb,var(--c) 55%,transparent),0 0 10px var(--c)}}70%,100%{{box-shadow:0 0 0 9px transparent,0 0 10px var(--c)}}}}
.hero-eyebrow::before{{--c:#5eead4;animation:glow 2.4s ease-out infinite}}
.market-status .gdot{{margin-right:0}}.mood-cap{{font-size:.85rem;opacity:.8}}.mood-cap .gdot{{margin-left:4px}}
.stat .d .gdot{{width:7px;height:7px;margin-right:6px}}
.market-status{{display:flex;align-items:center;gap:8px;width:max-content;max-width:100%;padding:7px 11px;margin:0 0 .7rem;border:1px solid rgba(94,234,212,.2);border-radius:999px;background:rgba(15,118,110,.16);color:#ccfbf1;font-size:.8rem}}
.mood{{height:12px;border-radius:99px;overflow:hidden;background:#ef4444;margin:.3rem 0 .2rem}}
.mood>div{{height:100%;background:#22c55e;transition:width .6s}}
button{{min-height:44px;border-radius:12px!important;transition:transform .15s ease,box-shadow .15s ease!important}}
button:hover{{transform:translateY(-1px);box-shadow:0 6px 18px rgba(0,0,0,.18)}}
button:focus-visible,a:focus-visible,input:focus-visible{{outline:3px solid #67e8f9!important;outline-offset:2px!important}}
.st-key-topnav div{{flex-wrap:wrap!important}}
.st-key-topnav button{{min-height:46px;font-weight:600;padding:0 16px}}
.stat-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:.25rem 0 .7rem}}
.stat{{background:linear-gradient(145deg,rgba(255,255,255,.11),rgba(255,255,255,.045));border:1px solid rgba(255,255,255,.13);border-radius:16px;padding:12px 14px;backdrop-filter:blur(10px);box-shadow:0 8px 24px rgba(0,0,0,.12)}}
.stat .l{{font-size:.74rem;opacity:.78;letter-spacing:.02em}}
.stat .v{{font-size:1.3rem;font-weight:700;line-height:1.3}}
.stat .d{{font-size:.8rem;font-weight:600}}
.stat .d.up{{color:#4ade80}}.stat .d.dn{{color:#f87171}}
.gf-head{{margin:.2rem 0 .4rem}}
.gf-title{{font-size:1.7rem;font-weight:500;line-height:1.25}}
.gf-sub{{font-size:.85rem;opacity:.75;margin-bottom:.5rem}}
.gf-row{{display:flex;align-items:center;flex-wrap:wrap;gap:6px 14px}}
.gf-price{{font-size:2.6rem;font-weight:400;line-height:1.1}}
.gf-cur{{font-size:1rem;opacity:.7;margin-left:6px}}
.gf-badge{{padding:4px 10px;border-radius:8px;font-weight:600;font-size:1rem}}
.gf-badge.up{{background:#81c995;color:#0b2e17}}.gf-badge.dn{{background:#f28b82;color:#3b0a08}}
.gf-today{{font-size:1rem;font-weight:500}}.gf-today.up{{color:#81c995}}.gf-today.dn{{color:#f28b82}}
.gf-time{{font-size:.78rem;opacity:.72;margin-top:4px}}
.gf-note{{font-size:.9rem;margin:.3rem 0 .2rem}}
.gf-note .up{{color:#81c995}}.gf-note .dn{{color:#f28b82}}
.gf{{display:grid;grid-template-rows:repeat(3,auto);grid-auto-flow:column;column-gap:40px;margin:.6rem 0 1rem}}
.gfr{{display:flex;justify-content:space-between;gap:14px;padding:7px 0;font-size:.95rem}}
.gfr .k{{opacity:.78}}.gfr .v{{font-weight:500}}
.ftab{{display:grid;grid-template-columns:1fr 1fr;column-gap:32px;margin:.2rem 0 .8rem}}
.fr{{display:flex;justify-content:space-between;gap:12px;padding:10px 2px;border-bottom:1px solid rgba(255,255,255,.09);font-size:.92rem}}
.fr .k{{opacity:.78}}.fr .v{{font-weight:600;text-align:right}}
.rb{{margin:.4rem 0 1rem}}
.rb .ends{{display:flex;justify-content:space-between;font-size:.8rem;opacity:.9;line-height:1.35}}
.rb .track{{position:relative;height:6px;border-radius:99px;background:linear-gradient(90deg,#ef4444,#f59e0b,#22c55e);margin:8px 0 2px}}
.rb .dot{{position:absolute;top:-5px;width:16px;height:16px;border-radius:50%;background:#fff;border:3px solid #0a0f1f;transform:translateX(-50%);box-sizing:border-box}}
/* phones: sidebar and its open/close arrows hidden (the top buttons are used instead). laptops and tablets: top buttons hidden (the sidebar is used) */
@media (max-width:768px){{[data-testid="stSidebar"],[data-testid="stSidebarCollapsedControl"],[data-testid="collapsedControl"],[data-testid="stExpandSidebarButton"],[data-testid="stSidebarCollapseButton"],[data-testid="stSidebarHeader"]{{display:none!important}}}}
@media (min-width:769px){{.st-key-topnav{{display:none!important}}}}
@media (max-width:640px){{.hero-title{{font-size:1.25rem;letter-spacing:.06em}}.brand img{{height:56px!important;width:56px!important}}
.block-container{{padding-left:.9rem;padding-right:.9rem;padding-top:2rem}}.brand{{padding:.9rem;gap:12px;border-radius:18px}}.stat-grid{{grid-template-columns:repeat(2,1fr)}}.stat .v{{font-size:1.1rem}}
.ftab{{grid-template-columns:1fr}}.gf{{grid-auto-flow:row;grid-template-rows:none;grid-template-columns:1fr}}
.gf-title{{font-size:1.25rem}}.gf-price{{font-size:2rem}}}}
@media (prefers-reduced-motion:reduce){{.gdot,.hero-eyebrow::before{{animation:none}}.stApp::before{{animation:none}}div[class*="st-key-card_"]{{transition:none}}}}
</style>""", unsafe_allow_html=True)


def video_background() -> None:
    """Full-screen looping hero video. Set VIDEO_URL = "" to switch it off.
    Laptop (wide screen): the video fills the screen under a dark overlay so the text stays readable.
    Phone (tall screen): the whole video is shown at the top, so the bull and bear are never cropped.
    People who ask their device for reduced motion get a plain dark background instead of the video."""
    if not VIDEO_URL:
        return
    st.markdown(f"""<style>
html,body{{background:#0a0f1f}}
.stApp,[data-testid="stAppViewContainer"],[data-testid="stHeader"]{{background:transparent!important}}
.stApp::before{{display:none}}
.hero-video{{position:fixed;top:0;left:0;width:100vw;height:100vh;object-fit:cover;z-index:-1;background:#0a0f1f}}
.hero-overlay{{position:fixed;inset:0;background:rgba(10,15,31,.72);z-index:-1}}
@media (max-aspect-ratio:1/1){{
.hero-video{{object-fit:contain;object-position:center top}}
.hero-overlay{{background:rgba(10,15,31,.2)}}
.block-container{{padding-top:calc(56.25vw + 1rem)!important}}
}}
@media (prefers-reduced-motion:reduce){{.hero-video{{display:none}}.hero-overlay{{background:#0a0f1f}}}}
</style>
<video class="hero-video" autoplay loop muted playsinline preload="metadata" aria-hidden="true">
<source src="{VIDEO_URL}" type="video/mp4"></video>
<div class="hero-overlay" aria-hidden="true"></div>""", unsafe_allow_html=True)


@lru_cache(maxsize=1)
def logo_html() -> str:
    try:
        b64 = base64.b64encode(LOGO_PATH.read_bytes()).decode()
        return f'<img src="data:image/png;base64,{b64}" alt="{ORG_NAME} logo" style="height:78px;width:78px;flex:none;border-radius:16px">'
    except OSError:
        return '<div style="font-size:3rem;flex:none">📈</div>'  # logo.png missing: fall back to an emoji


def header() -> None:
    st.markdown(f'<div class="brand">{logo_html()}<div><div class="hero-eyebrow">INDIAN MARKETS, EXPLAINED</div>'
                f'<div class="hero-title">{ORG_NAME}</div>'
                f'<div class="hero-sub" style="margin:.15rem 0 0">{ORG_SUBTITLE} · {TAGLINE}</div></div></div>',
                unsafe_allow_html=True)


def mood_bar(rows: list) -> None:
    if not rows:
        return
    up = sum(1 for r in rows if r[3] > 0)
    st.markdown(f'<div class="mood"><div style="width:{up / len(rows) * 100:.0f}%"></div></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="mood-cap">Market mood: <span class="gdot g"></span>{up} up &nbsp;<span class="gdot r"></span>{len(rows) - up} down '
                f'among {len(rows)} large companies tracked</div>', unsafe_allow_html=True)


def stat_grid(items: list[tuple]) -> None:
    """Responsive tiles: 4 across on a laptop, 2 across on a phone. items = (label, value, pct change or None, tooltip)."""
    cells = []
    for label, value, pct, tip in items:
        delta = ""
        if pct is not None:
            delta = (f'<div class="d {"up" if pct >= 0 else "dn"}"><span class="gdot {"g" if pct >= 0 else "r"}"></span>'
                     f'{"▲" if pct >= 0 else "▼"} {pct:+.2f}%</div>')
        cells.append(f'<div class="stat" title="{html.escape(tip, quote=True)}"><div class="l">{html.escape(label)}</div>'
                     f'<div class="v">{html.escape(value)}</div>{delta}</div>')
    st.markdown(f'<div class="stat-grid">{"".join(cells)}</div>', unsafe_allow_html=True)


def metrics_row(prices: dict) -> None:
    stat_grid([(label, f"{v[0]:,.2f}" if v else "—", v[1] if v else None,
                "Change vs previous close. Green = up, red = down." if v else "Data unavailable right now.")
               for label, tk in INDICES.items() for v in [prices.get(tk)]])


SIDEBAR_CSS = """<style>
[data-testid="stSidebar"]{background:rgba(10,15,31,.94);border-right:1px solid rgba(255,255,255,.08)}
[data-testid="stSidebar"] [role="radiogroup"]{gap:4px}
[data-testid="stSidebar"] [role="radiogroup"] label{padding:10px 12px;border-radius:10px;width:100%;cursor:pointer}
[data-testid="stSidebar"] [role="radiogroup"] label:hover{background:rgba(255,255,255,.07)}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked){background:rgba(109,74,255,.28)}
[data-testid="stSidebar"] [role="radiogroup"] label>div:first-child{display:none}
.side-brand{font-weight:800;letter-spacing:.1em;font-size:1.1rem;margin:.2rem 0 .8rem}
.side-brand small{display:block;font-weight:400;letter-spacing:.02em;opacity:.7;font-size:.75rem}
</style>"""
