"""A calm one-question-at-a-time daily CA Intermediate practice screen."""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import streamlit as st

from backend.daily_practice import DAILY_TARGET, count_correct, daily_questions

INDIA = ZoneInfo("Asia/Kolkata")


def render_daily_practice() -> None:
    today = datetime.now(INDIA).date()
    questions = daily_questions(today)
    session_key = "daily_practice_" + today.isoformat()
    if session_key not in st.session_state:
        st.session_state[session_key] = {"answers": {}, "position": 0}
    state = st.session_state[session_key]
    answers = state["answers"]
    progress = len(answers)
    st.subheader("Your daily 20-minute practice")
    st.caption(
        "20 questions × 1 mark · CA Intermediate · India calendar day · "
        "Original practice questions, not official ICAI exam questions. "
        "This starter bank has not yet been verified by an independent CA faculty reviewer."
    )
    st.progress(progress / DAILY_TARGET, text=f"{progress} of {DAILY_TARGET} answered · {progress}/{DAILY_TARGET} marks attempted")
    col1, col2, col3 = st.columns(3)
    col1.metric("Questions", str(DAILY_TARGET))
    col2.metric("Answered", str(progress))
    col3.metric("Score so far", f"{count_correct(questions, answers)}/{DAILY_TARGET}")
    if progress == DAILY_TARGET:
        st.success(f"Practice complete! Your score: {count_correct(questions, answers)}/{DAILY_TARGET}")
        st.caption("Review every explanation below. Your completion is stored in this browser session only.")
        for i, question in enumerate(questions, 1):
            with st.expander(f"{i}. {question.subject} · {'Correct' if answers.get(question.id) == question.answer_index else 'Review'}"):
                st.write(question.prompt)
                st.write("Your choice: " + question.options[answers[question.id]])
                st.write("Answer: " + question.options[question.answer_index])
                st.info(question.explanation)
        return

    # Show the first unanswered question, rather than an index that can become stale.
    question = next(q for q in questions if q.id not in answers)
    number = progress + 1
    with st.container(border=True):
        st.caption(f"QUESTION {number} OF {DAILY_TARGET} · {question.subject} · 1 MARK")
        st.markdown(f"#### {question.prompt}")
        with st.form(f"daily_answer_{today}_{question.id}"):
            choice = st.radio(
                "Choose one answer",
                options=tuple(range(4)),
                format_func=lambda i: question.options[i],
                index=None,
                key=f"daily_choice_{today}_{question.id}",
            )
            submitted = st.form_submit_button("Submit answer", type="primary", use_container_width=True)
        if submitted:
            if choice is None:
                st.warning("Choose one option before submitting.")
            else:
                answers[question.id] = int(choice)
                st.rerun()
        st.caption("Your answer is locked once submitted. You can review every solution at the end.")

    with st.expander("Study tips"):
        st.write("Read the full question, identify the concept, then compare the four options. "
                 "Record mistakes in your notes and retry the topic. Scores reset on a new India-local date.")
