"""Intellics: page setup, navigation and the main() entry point."""
from __future__ import annotations
import html

from companies import COMPANIES
from PIL import Image
import streamlit as st
import trading_game

from config import FEEDBACK_URL, INDICES, LOGO_PATH, NEWS_REFRESH, ORG_NAME, PRICE_REFRESH, SOURCES, TAGLINE, VERSION
from corporate import corporate_tab
from learn import quiz_tab, terms_tab
from markets import focus_section, movers_section, price_bar
from news import load_news
from news_page import filter_bar, init_state, news_section
from prices import all_tickers, load_prices
from ui import SIDEBAR_CSS, header, inject_css, video_background


try:
    PAGE_ICON = Image.open(LOGO_PATH)
except Exception:
    PAGE_ICON = "📈"


# "auto" = sidebar open on laptops/tablets, folded away on phones (phones get the top buttons instead)
st.set_page_config(page_title="Intellics Committee", page_icon=PAGE_ICON, layout="wide", initial_sidebar_state="auto")


def about_tab() -> None:
    st.subheader("ℹ️ About Intellics")
    st.markdown("Intellics is a student project that explains Indian market news and prices in plain English. "
                "It is free to use and built only with free tools.")
    st.markdown("**Where the data comes from**")
    st.markdown("- **News:** " + ", ".join(SOURCES) + ". Google News results are kept only if the publisher is on our trusted list. "
                "We link to the original article and never copy it.\n"
                "- **Prices and company numbers:** Yahoo Finance (free, unofficial).\n"
                "- **Dividends, splits and bonus issues:** NSE India, with a Yahoo backup.")
    st.markdown("**How often it updates**")
    st.markdown(f"- News: about every {NEWS_REFRESH // 60} minutes.\n- Prices: about every {PRICE_REFRESH} seconds. "
                "The page always shows the time of the latest data point, so you can see how fresh it is.")
    st.markdown("**How the summaries work**")
    st.markdown("Each summary is written automatically from the headline and the short preview, not the full article. "
                "When a free AI service is available it writes the summary; otherwise a simple rule-based version is used. "
                "Either way it can miss details, so please open the original article.")
    st.markdown("**Known limits**")
    st.markdown("- Free data can be delayed, incomplete or briefly unavailable. A dash (—) means *not available*, not zero.\n"
                f"- About {len(COMPANIES)} large companies are tracked, not the whole market.\n"
                "- The Trading Challenge uses play money and delayed prices. It is a game, not advice.\n"
                "- Nothing here is investment advice. See the disclaimer below.")
    st.markdown(f"**What's new in {VERSION}:** Trading Challenge with weekly, monthly and overall leaderboards and titles "
                "(top 10 overall, top 3 weekly and monthly), a left sidebar menu, many more companies, sector heatmap, "
                "terms quiz, this About page.")
    if FEEDBACK_URL:
        st.link_button("Found a problem or have an idea? Tell us", FEEDBACK_URL)
    else:
        st.caption("Feedback form coming soon.")


DISCLAIMER = """**Disclaimer**

Intellics is a student learning project made for educational purposes only. Nothing on this page is investment, financial, legal or tax advice, and nothing here is a recommendation or an offer to buy, sell or hold any security. The creators are not SEBI-registered investment advisers or research analysts.

- **Prices and data** come from free third-party sources (Yahoo Finance). They may be delayed, incomplete or wrong, and may differ from the exchange, your broker or other apps. Always check the official NSE/BSE data or your broker before making any decision.
- **News** belongs to its publishers and is linked, not reproduced. The short summaries are generated automatically from each headline and preview (not the full article), so they can miss details or contain mistakes. Please open the original article.
- **Investing in shares carries risk,** including loss of money. Past performance does not guarantee future results. Please speak to a SEBI-registered adviser before investing.
- This project is provided as is, without any guarantee, and the creators accept no liability for any loss arising from its use."""


# ------------------------------------------------------------- navigation
PAGES = {"news": "📰 News", "markets": "📈 Markets", "learn": "🎓 Learn", "game": "🏆 Trading game"}


def _side_changed() -> None:
    st.session_state["nav_top"] = st.session_state["nav_side"]


def _top_changed() -> None:
    ss = st.session_state
    if ss.get("nav_top"):                 # tapping the chosen button again would clear it, so keep the old page then
        ss["nav_side"] = ss["nav_top"]
    ss["nav_top"] = ss["nav_side"]


def navigation() -> str:
    """Laptops and tablets: a menu in the left sidebar (like a dashboard). Phones: tappable buttons at the top
    that wrap onto several lines, so nothing is hidden off-screen. Both menus stay in step with each other, and the
    chosen page is stored in the web address (?page=learn), so a section can be bookmarked or shared."""
    ss = st.session_state
    labels, slugs = list(PAGES.values()), {v: k for k, v in PAGES.items()}
    if ss.get("nav_side") not in labels:
        ss["nav_side"] = PAGES.get(str(st.query_params.get("page") or ""), labels[0])
    if ss.get("nav_top") not in labels:
        ss["nav_top"] = ss["nav_side"]
    st.markdown(SIDEBAR_CSS, unsafe_allow_html=True)
    with st.sidebar:
        st.markdown(f'<div class="side-brand">📊 {html.escape(ORG_NAME.split()[0].upper())}<small>{html.escape(TAGLINE)}</small></div>',
                    unsafe_allow_html=True)
        st.radio("Go to", labels, key="nav_side", label_visibility="collapsed", on_change=_side_changed)
    with st.container(key="topnav"):
        st.pills("Go to", labels, selection_mode="single", key="nav_top", label_visibility="collapsed", on_change=_top_changed)
    page = slugs[ss["nav_side"]]
    if st.query_params.get("page") != page:
        st.query_params["page"] = page
    return page


def game_page() -> None:
    """The Trading Challenge page (code lives in trading_game.py)."""
    trading_game.game_tab({n: tk for n, (tk, _) in COMPANIES.items()},
                          lambda: load_prices(all_tickers()), INDICES["Nifty 50"])


def markets_page() -> None:
    """Gainers & losers, Stocks in focus and Dividends & splits, grouped on one page."""
    view = st.pills("Markets view", ["Gainers & losers", "Stocks in focus", "Dividends & splits"],
                    selection_mode="single", default="Gainers & losers", key="markets_view",
                    label_visibility="collapsed") or "Gainers & losers"
    if view == "Gainers & losers":
        movers_section()
    elif view == "Stocks in focus":
        focus_section()
    else:
        corporate_tab()


def learn_page() -> None:
    """Financial terms and the quiz, grouped on one page."""
    view = st.pills("Learn view", ["Financial terms", "Quiz"], selection_mode="single",
                    default="Financial terms", key="learn_view",
                    label_visibility="collapsed") or "Financial terms"
    if view == "Financial terms":
        terms_tab(load_news()[0])
    else:
        quiz_tab()


def main() -> None:
    init_state()
    # Closes the Trading Challenge week by itself once Saturday 00:00 IST has passed. It does nothing on weekdays,
    # never raises, and works on any page, so a keep-alive visit to the app is enough to trigger it.
    trading_game.auto_close_if_due(lambda: load_prices(all_tickers()), [tk for tk, _ in COMPANIES.values()])
    inject_css()
    video_background()
    header()
    price_bar()
    page = navigation()
    if page == "news":
        filter_bar()
        news_section()
    elif page == "markets":
        markets_page()
    elif page == "learn":
        learn_page()
    else:
        game_page()
    with st.expander("ℹ️ About Intellics"):
        about_tab()
    st.divider()
    st.caption(DISCLAIMER)
    st.caption(f"{ORG_NAME} {VERSION}")
    if FEEDBACK_URL:
        st.link_button("Found a problem? Tell us", FEEDBACK_URL)


main()
