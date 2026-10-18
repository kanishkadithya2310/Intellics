"""Intellics: UI module with a soft header glow and teal live-status light."""
from __future__ import annotations

import base64
import html
from functools import lru_cache
from pathlib import Path

import streamlit as st

try:
    from config import (
        BACKGROUND_IMAGE_URL,
        INDICES,
        LOGO_PATH,
        ORG_NAME,
        ORG_SUBTITLE,
        TAGLINE,
        VIDEO_URL,
    )
except ImportError:
    BACKGROUND_IMAGE_URL = ""
    VIDEO_URL = "https://cdn.jsdelivr.net/gh/kanishkadithya2310/Intellics@main/hero.mp4"
    LOGO_PATH = Path(__file__).parent / "logo.png"
    ORG_NAME = "Intellics Committee"
    ORG_SUBTITLE = "The AI and Data Analytics Committee"
    TAGLINE = "Think | Analyze | Evolve"
    INDICES = {
        "Sensex": "^BSESN",
        "Nifty 50": "^NSEI",
        "Brent crude (USD/bbl)": "BZ=F",
        "Gold (USD/oz)": "GC=F",
    }


def inject_css() -> None:
    photo = (
        f"linear-gradient(rgba(8,12,28,.82),rgba(8,12,28,.9)),"
        f"url('{BACKGROUND_IMAGE_URL}') center/cover fixed"
        if BACKGROUND_IMAGE_URL
        else ""
    )

    st.markdown(f"""<style>
.stApp{{background:{photo or 'radial-gradient(1100px 600px at 8% -10%,#1d3157 0%,transparent 60%),radial-gradient(900px 520px at 100% 0%,#3b1d5e 0%,transparent 55%),#0a0f1f fixed'};}}

.stApp::before{{
    content:""; position:fixed; inset:0; pointer-events:none; z-index:0;
    background-image:
        linear-gradient(rgba(255,255,255,.03) 1px,transparent 1px),
        linear-gradient(90deg,rgba(255,255,255,.03) 1px,transparent 1px);
    background-size:42px 42px;
    animation:drift 40s linear infinite;
}}

@keyframes drift{{to{{background-position:42px 42px}}}}

.block-container{{padding-top:3.2rem;max-width:1180px;position:relative;z-index:1}}

.hero-title{{
    font-size:2rem;
    font-weight:800;
    letter-spacing:.12em;
    line-height:1.15;
    margin:0;
}}

.brand{{
    position:relative;
    overflow:hidden;
    display:flex;
    align-items:center;
    gap:16px;
    margin:0 0 1.15rem;
    padding:1.15rem 1.3rem;
    background:linear-gradient(120deg,rgba(28,45,82,.82),rgba(45,26,76,.68));
    border:1px solid rgba(184,205,255,.18);
    border-radius:22px;
    box-shadow:0 18px 55px rgba(0,0,0,.22);
}}

/* Purple glow */
.brand::after{{
    content:"";
    position:absolute;
    width:240px;
    height:240px;
    right:-90px;
    top:-150px;
    border-radius:50%;
    background:rgba(115,126,255,.18);
    filter:blur(4px);
    pointer-events:none;
}}

.brand > *{{position:relative;z-index:1}}

.hero-eyebrow{{
    display:inline-flex;
    align-items:center;
    gap:7px;
    font-size:.68rem;
    font-weight:700;
    letter-spacing:.13em;
    color:#c7d2fe;
    margin-bottom:.34rem;
}}

/* Teal light */
.hero-eyebrow::before{{
    content:"";
    width:7px;
    height:7px;
    border-radius:50%;
    background:#5eead4;
    box-shadow:0 0 12px #5eead4;
}}

.hero-sub{{opacity:.85;margin-bottom:.6rem}}

.stat-grid{{
    display:grid;
    grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
    gap:12px;
    margin:.25rem 0 .7rem;
}}

.stat{{
    background:linear-gradient(145deg,rgba(255,255,255,.11),rgba(255,255,255,.045));
    border:1px solid rgba(255,255,255,.13);
    border-radius:16px;
    padding:12px 14px;
    backdrop-filter:blur(10px);
    box-shadow:0 8px 24px rgba(0,0,0,.12);
}}

.stat .l{{font-size:.74rem;opacity:.78}}
.stat .v{{font-size:1.3rem;font-weight:700;line-height:1.3}}
.stat .d{{font-size:.8rem;font-weight:600}}
.stat .d.up{{color:#4ade80}}
.stat .d.dn{{color:#f87171}}

button{{
    min-height:44px;
    border-radius:12px!important;
    transition:transform .15s ease,box-shadow .15s ease!important;
}}

button:hover{{
    transform:translateY(-1px);
    box-shadow:0 6px 18px rgba(0,0,0,.18);
}}

button:focus-visible,a:focus-visible,input:focus-visible{{
    outline:3px solid #67e8f9!important;
    outline-offset:2px!important;
}}

@media (max-width:640px){{
    .hero-title{{font-size:1.25rem;letter-spacing:.06em}}
    .brand img{{height:56px!important;width:56px!important}}
    .block-container{{padding-left:.9rem;padding-right:.9rem;padding-top:2rem}}
    .brand{{padding:.9rem;gap:12px;border-radius:18px}}
    .stat-grid{{grid-template-columns:repeat(2,1fr)}}
    .stat .v{{font-size:1.1rem}}
}}
</style>""", unsafe_allow_html=True)


def video_background() -> None:
    if not VIDEO_URL:
        return

    st.markdown(f"""<style>
html,body{{background:#0a0f1f}}
.stApp,[data-testid="stAppViewContainer"],[data-testid="stHeader"]{{
    background:transparent!important;
}}
.stApp::before{{display:none}}

.hero-video{{
    position:fixed;
    top:0;
    left:0;
    width:100vw;
    height:100vh;
    object-fit:cover;
    z-index:-1;
    background:#0a0f1f;
}}

.hero-overlay{{
    position:fixed;
    inset:0;
    background:rgba(10,15,31,.72);
    z-index:-1;
}}

@media (prefers-reduced-motion:reduce){{
    .hero-video{{display:none}}
    .hero-overlay{{background:#0a0f1f}}
}}
</style>

<video class="hero-video" autoplay loop muted playsinline preload="metadata" aria-hidden="true">
    <source src="{VIDEO_URL}" type="video/mp4">
</video>
<div class="hero-overlay" aria-hidden="true"></div>
""", unsafe_allow_html=True)


@lru_cache(maxsize=1)
def logo_html() -> str:
    try:
        b64 = base64.b64encode(LOGO_PATH.read_bytes()).decode()
        return (
            f'<img src="data:image/png;base64,{b64}" '
            f'alt="{ORG_NAME} logo" '
            f'style="height:78px;width:78px;flex:none;border-radius:16px">'
        )
    except OSError:
        return '<div style="font-size:3rem;flex:none">📈</div>'


def header() -> None:
    st.markdown(
        f'<div class="brand">{logo_html()}'
        f'<div>'
        f'<div class="hero-eyebrow">INDIAN MARKETS, EXPLAINED</div>'
        f'<div class="hero-title">{ORG_NAME}</div>'
        f'<div class="hero-sub" style="margin:.15rem 0 0">'
        f'{ORG_SUBTITLE} · {TAGLINE}'
        f'</div></div></div>',
        unsafe_allow_html=True,
    )


def stat_grid(items: list[tuple]) -> None:
    cells = []

    for label, value, pct, tip in items:
        delta = ""
        if pct is not None:
            direction = "up" if pct >= 0 else "dn"
            arrow = "▲" if pct >= 0 else "▼"
            delta = f'<div class="d {direction}">{arrow} {pct:+.2f}%</div>'

        cells.append(
            f'<div class="stat" title="{html.escape(tip, quote=True)}">'
            f'<div class="l">{html.escape(label)}</div>'
            f'<div class="v">{html.escape(value)}</div>'
            f'{delta}</div>'
        )

    st.markdown(f'<div class="stat-grid">{"".join(cells)}</div>', unsafe_allow_html=True)


def metrics_row(prices: dict) -> None:
    stat_grid([
        (
            label,
            f"{value[0]:,.2f}" if value else "—",
            value[1] if value else None,
            "Change versus previous close." if value else "Data unavailable right now.",
        )
        for label, ticker in INDICES.items()
        for value in [prices.get(ticker)]
    ])



