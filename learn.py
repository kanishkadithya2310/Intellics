"""Intellics: learn module (split out of app.py)."""
from __future__ import annotations
from collections import Counter
from datetime import date, datetime, timedelta
import random

import streamlit as st

from config import IST, TERMS
from helpers import glossary_hits, md_safe, small


# ------------------------------------------------------------ financial terms
TERMS_PER_DAY = 10


def terms_for(day: date) -> list[dict]:
    """Today's 10 terms. The list is walked in a fixed order, so nothing repeats until every block has been shown."""
    days = len(TERMS) // TERMS_PER_DAY
    if not days:
        return []
    start = (day.toordinal() % days) * TERMS_PER_DAY
    return TERMS[start:start + TERMS_PER_DAY]


def term_block(i: int, t: dict) -> None:
    st.markdown(f"**{i}. {md_safe(t['term'])}** :blue-badge[{md_safe(t['cat'])}]  \n{md_safe(t['meaning'])}  \n"
                f"*Example: {md_safe(t['example'])}*")


def terms_tab(stories: list[dict]) -> None:
    days = len(TERMS) // TERMS_PER_DAY
    if not days:
        st.info("The terms list wasn't found. Upload terms.py next to app.py in your GitHub repo.")
        return
    today = datetime.now(IST).date()
    st.subheader(f"🧠 10 terms of the day · {today:%A, %d %B %Y}")
    st.caption(f"{len(TERMS)} unique terms, shown in a fixed order, so nothing repeats for {days} days.")
    for i, t in enumerate(terms_for(today), 1):
        term_block(i, t)

    counts, meaning = Counter(), {}
    for s in stories[:100]:
        for name, m in glossary_hits(f"{s['title']} {s['summary']}"):
            counts[name] += 1
            meaning[name] = m
    if counts:
        st.subheader("📰 Terms in today's news")
        for name, n in counts.most_common(6):
            used = f"in {n} " + ("story" if n == 1 else "stories")
            st.markdown(f"**{md_safe(name)}**: {md_safe(meaning[name])}  \n{small(used)}", unsafe_allow_html=True)

    with st.expander("⏮ Previous days"):
        back = st.slider("Days back", 1, 7, 1, key="terms_back")
        day = today - timedelta(days=back)
        st.markdown(f"**{day:%A, %d %B}**")
        for i, t in enumerate(terms_for(day), 1):
            term_block(i, t)
    with st.expander(f"📖 Browse all {len(TERMS)} terms"):
        a, b = st.columns([2, 1])
        q = a.text_input("Search terms", key="terms_q", placeholder="🔎 Search a term").strip().lower()
        cat = b.selectbox("Topic", ["All"] + sorted({t["cat"] for t in TERMS}), key="terms_cat")
        hits = [t for t in sorted(TERMS, key=lambda t: t["term"].lower())
                if (cat == "All" or t["cat"] == cat) and (not q or q in f"{t['term']} {t['meaning']}".lower())]
        st.caption(f"{len(hits)} matching terms" + (" (showing the first 40)" if len(hits) > 40 else ""))
        for i, t in enumerate(hits[:40], 1):
            term_block(i, t)


QUIZ_LEN = 5


def quiz_pool() -> list[dict]:
    return [t for t in TERMS if t.get("term") and t.get("meaning")]


def new_quiz() -> None:
    """Pick 5 random terms. Wrong answers come from the same topic where possible, so they look believable."""
    rng, pool, qs = random.Random(), quiz_pool(), []
    for t in rng.sample(pool, min(QUIZ_LEN, len(pool))):
        same = [x for x in pool if x["term"] != t["term"] and x.get("cat") == t.get("cat")]
        other = [x for x in pool if x["term"] != t["term"] and x.get("cat") != t.get("cat")]
        wrong = rng.sample(same, min(3, len(same)))
        wrong += rng.sample(other, min(3 - len(wrong), len(other)))
        opts = [t["term"]] + [w["term"] for w in wrong]
        rng.shuffle(opts)
        qs.append({"term": t["term"], "meaning": t["meaning"], "example": t.get("example", ""), "opts": opts})
    st.session_state["quiz"] = {"qs": qs, "i": 0, "score": 0, "checked": False, "pick": None, "id": rng.randrange(10**9)}


def quiz_check() -> None:
    ss = st.session_state
    quiz = ss["quiz"]
    pick = ss.get(f"qpick_{quiz['id']}_{quiz['i']}")
    if pick is None:  # nothing chosen yet
        return
    quiz["checked"], quiz["pick"] = True, pick
    if pick == quiz["qs"][quiz["i"]]["term"]:
        quiz["score"] += 1
        ss["quiz_streak"] = ss.get("quiz_streak", 0) + 1
        ss["quiz_best"] = max(ss.get("quiz_best", 0), ss["quiz_streak"])
    else:
        ss["quiz_streak"] = 0


def quiz_next() -> None:
    quiz = st.session_state["quiz"]
    quiz["i"] += 1
    quiz["checked"], quiz["pick"] = False, None


def quiz_tab() -> None:
    st.subheader("🎯 Terms quiz")
    if len(quiz_pool()) < 10:
        st.info("The terms list wasn't found. Upload terms.py next to app.py in your GitHub repo.")
        return
    ss = st.session_state
    quiz = ss.get("quiz")
    if not quiz:
        st.write(f"{QUIZ_LEN} quick questions from our {len(TERMS)} finance terms. Read the meaning, pick the right term.")
        st.button("Start quiz", on_click=new_quiz, key="quiz_start")
        return
    n = len(quiz["qs"])
    if quiz["i"] >= n:
        st.success(f"You scored {quiz['score']} out of {n}.")
        st.caption(f"Best streak this visit: {ss.get('quiz_best', 0)} correct in a row")
        st.button("Play again", on_click=new_quiz, key="quiz_again")
        return
    q = quiz["qs"][quiz["i"]]
    st.progress(quiz["i"] / n, text=f"Question {quiz['i'] + 1} of {n} · score {quiz['score']} · streak {ss.get('quiz_streak', 0)}")
    st.markdown(f"**Which term means:** {md_safe(q['meaning'])}")
    st.radio("Choose one", q["opts"], index=None, key=f"qpick_{quiz['id']}_{quiz['i']}",
             disabled=quiz["checked"], label_visibility="collapsed")
    if not quiz["checked"]:
        st.button("Check answer", on_click=quiz_check, key="quiz_check")
        return
    if quiz["pick"] == q["term"]:
        st.success(f"Correct! It's {q['term']}.")
    else:
        st.error(f"Not quite. The answer is {q['term']}.")
    if q["example"]:
        st.caption(f"Example: {q['example']}")
    st.button("Next question" if quiz["i"] < n - 1 else "See my score", on_click=quiz_next, key="quiz_next")
