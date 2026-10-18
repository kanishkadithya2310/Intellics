# Intellics

Indian markets news, explained simply. A student learning project by the Intellics Committee
(IFMR GSB). Built with Streamlit.

## What it does
- Trusted-source market news with plain-English summaries
- Live-ish prices, gainers and losers, a company page with charts and fundamentals
- Upcoming dividends, splits and bonus issues
- Financial terms, a quiz and a virtual-money Trading Challenge

## Run it locally
```bash
pip install -r requirements-dev.txt
streamlit run app.py
```

## Run the tests
```bash
pytest
ruff check .
```

## Project layout
| File | Purpose |
|---|---|
| `app.py` | Page setup, navigation, `main()` (must stay the last line) |
| `config.py` | Settings, source lists, constants |
| `helpers.py` | Text helpers and shared store |
| `news.py`, `summaries.py` | Feeds, stories, summaries |
| `prices.py` | Price data and market status |
| `ui.py` | CSS, header, stat tiles, glowing status dots |
| `news_page.py`, `markets.py`, `company.py`, `corporate.py`, `learn.py` | Pages and tabs |
| `companies.py`, `terms.py`, `trading_game.py` | Data and the trading game |

## Secrets
Keys (Groq, Supabase) go in Streamlit **Secrets**, never in the repo. Locally they live in
`.streamlit/secrets.toml`, which is git-ignored.

## Disclaimer
Educational only. Not investment advice. Data comes from free third-party sources and can be
delayed or wrong.
