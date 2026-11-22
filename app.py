"""CA tutor: local Streamlit workspace. Run with python -m streamlit run app.py."""

import json

import streamlit as st

from backend.demo import SAMPLE_QUESTION, build_demo_response, prepared_example
from backend.session import StudyContext, append_exchange, export_chat, timestamp
from backend.ai_engine import TutorService
from backend.errors import AppError
from ui.runtime import settings as load_app_settings, access_gate, runtime, ledger
from ui.library import render_library
from ui.calculations import render_calculator
from ui.daily_practice import render_daily_practice
from ui.dataset_status import render_dataset_status
from config.catalog import (
    ANSWER_FORMATS,
    APP_TITLE,
    CATALOG,
    MAX_QUESTION_CHARS,
    MAX_TURNS,
    MVP_CHAPTER,
)

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Only static, developer-authored HTML/CSS is rendered with unsafe_allow_html.
st.markdown(
    """
    <style>
    .block-container { max-width: 1220px; padding-top: 2rem; padding-bottom: 3rem; }
    .ca-brand { display: flex; gap: .8rem; align-items: center; margin: .2rem 0 1.5rem; }
    .ca-mark { background: #0f766e; color: white; border-radius: 12px; padding: .65rem;
               font-size: 1.15rem; font-weight: 750; letter-spacing: -.04em; }
    .ca-brand strong { font-size: 1.15rem; }
    .ca-brand small { display: block; font-size: .85rem; opacity: .7; margin-top: .15rem; }
    .ca-hero { background: linear-gradient(115deg, #173b38, #315b56); color: #fff;
               border-radius: 20px; padding: 2rem 2.2rem; margin: .5rem 0 1.5rem; }
    .ca-eyebrow { font-size: .8rem; letter-spacing: .13em; font-weight: 700;
                  text-transform: uppercase; color: #a7f3d0; margin-bottom: .8rem; }
    .ca-hero h1 { font-size: clamp(1.9rem, 3.6vw, 2.8rem); line-height: 1.15;
                  letter-spacing: -.04em; padding: 0; margin: 0 0 .8rem; color: white; }
    .ca-hero p { max-width: 650px; margin: 0; color: #dce9ed; font-size: 1rem; }
    [data-testid="stChatMessage"] { border-radius: 14px; }
    div[data-testid="stText"] { white-space: pre-wrap; overflow-wrap: anywhere; }
    @media (max-width: 640px) {
        .ca-hero { padding: 1.4rem; }
        .block-container { padding-left: 1rem; padding-right: 1rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def initialize_session() -> None:
    for key, initial in (
        ("messages", []),
        ("feedback", {}),
        ("issues", []),
    ):
        if key not in st.session_state:
            st.session_state[key] = initial


def clear_chat() -> None:
    st.session_state.messages = []
    st.session_state.feedback = {}
    for key in list(st.session_state):
        if str(key).startswith("vote_"):
            del st.session_state[key]


def reset_subject() -> None:
    st.session_state.pop("subject", None)
    st.session_state.pop("chapter", None)


def reset_chapter() -> None:
    st.session_state.pop("chapter", None)


def record_feedback(message_id: str) -> None:
    value = st.session_state.get(f"vote_{message_id}")
    if value is None:
        st.session_state.feedback.pop(message_id, None)
    else:
        st.session_state.feedback[message_id] = "helpful" if value == 1 else "not_helpful"


def add_turn(question: str, context: StudyContext, *, example: bool = False) -> None:
    metadata = {}
    if example:
        answer, kind = prepared_example(context.answer_format), "prepared_example"
    else:
        configuration = load_app_settings()
        provider, knowledge = runtime(configuration)
        if configuration.api_enabled and not st.session_state.get("provider_consent", False):
            raise AppError("Enable provider consent in the sidebar before sending questions or excerpts.", "consent")
        result = TutorService(configuration, knowledge, provider).ask(
            question, context, st.session_state.messages,
            require_sources=st.session_state.get("require_sources", False),
        )
        answer, kind = result.content, result.kind
        metadata = {"sources": result.sources, "status": result.status, "calculation": result.calculation}
    st.session_state.messages = append_exchange(
        st.session_state.messages, question, answer, context, kind=kind,
    )
    st.session_state.messages[-1].update(metadata)
    retained_ids = {message["id"] for message in st.session_state.messages}
    st.session_state.feedback = {
        key: value for key, value in st.session_state.feedback.items() if key in retained_ids
    }


def sidebar() -> StudyContext:
    with st.sidebar:
        st.markdown(
            '<div class="ca-brand"><div class="ca-mark">CA</div><div>'
            '<strong>CA AI Assistant</strong><small>Your study workspace</small></div></div>',
            unsafe_allow_html=True,
        )
        st.subheader("Make it your syllabus")
        st.caption("Choose the context for your next question.")
        level = st.selectbox(
            "CA level", tuple(CATALOG), index=1, key="level", on_change=reset_subject
        )
        subjects = tuple(CATALOG[level])
        subject = st.selectbox(
            "Subject", subjects, key="subject", on_change=reset_chapter
        )
        chapter = st.selectbox("Chapter / topic", CATALOG[level][subject], key="chapter")
        attempt = st.text_input(
            "Examination attempt",
            placeholder="Enter your planned attempt",
            max_chars=64,
            key="attempt",
            help="A study label only. Syllabus and amendment applicability are not verified yet.",
        ).strip()
        language = st.selectbox("Explanation language", ("English", "Tamil"), key="language")
        st.caption("Tamil narrative explanations require a configured AI provider; calculation notes remain in English.")
        answer_format = st.selectbox("Answer format", ANSWER_FORMATS, index=1, key="answer_format")
        with st.expander("Applicability and privacy"):
            assessment_year = st.text_input("Assessment year", key="assessment_year", max_chars=32)
            fiscal_year = st.text_input("Financial year", key="fiscal_year", max_chars=32)
            as_of = st.text_input("Effective date (YYYY-MM-DD)", key="as_of", max_chars=10)
            st.checkbox("Require applicable document evidence", key="require_sources")
            st.checkbox("Allow my questions and retrieved excerpts to be sent to the configured AI provider", key="provider_consent")
        st.divider()
        st.button(
            "Clear chat",
            key="clear_chat",
            icon=":material/delete_outline:",
            on_click=clear_chat,
            disabled=not st.session_state.messages,
            width="stretch",
        )
        st.caption(
            f"History stays in this session (up to {MAX_TURNS} exchanges). "
            "Refreshing, closing the tab, or restarting the server may reset it. "
            "Download it before leaving."
        )
        st.caption("Local workspace · AI and knowledge tools")
    return StudyContext(
        level, subject, chapter, attempt or "Not specified", language, answer_format,
        assessment_year.strip(), fiscal_year.strip(), as_of.strip(),
    )


def render_message(message: dict) -> None:
    with st.chat_message(message["role"]):
        if message["role"] == "user":
            # Display student input as text; do not render HTML or remote Markdown images.
            st.text(message["content"])
        else:
            st.markdown(message["content"])
            with st.expander("Sources and answer status"):
                st.text("Status: " + message.get("status", message["kind"]))
                sources = message.get("sources", [])
                for source in sources:
                    meta = source["metadata"]
                    st.caption("Search engine: " + source.get("search_engine", "faiss"))
                    st.text(f"[{source['source_id']}] {meta['title']} | {meta['chapter']}\n"
                            f"Pages {source['page_start']}–{source['page_end']} | version {meta['version']} | attempt {meta['attempt']}")
                    st.code(source.get("evidence_quote", source["text"])[:1600], language=None)
                if not sources:
                    st.write("No source document is cited for this reply.")
                st.caption("Source checks verify IDs and quoted passages, not the correctness of every interpretation. Calculations verify arithmetic for stated inputs.")
            st.feedback(
                "thumbs",
                key=f"vote_{message['id']}",
                on_change=record_feedback,
                args=(message["id"],),
            )
        context = message["context"]
        st.caption("Study context when this message was sent")
        st.text(
            f"{context['level']} · {context['subject']}\n"
            f"{context['chapter']} · Attempt: {context['attempt']}\n"
            f"{context['answer_format']} · {context['language']}"
        )


def tutor_tab(context: StudyContext) -> None:
    main, companion = st.columns([2.2, 1], gap="large")
    with companion:
        with st.container(border=True):
            st.subheader("Today's focus")
            st.write(context.subject)
            st.text(context.chapter)
            st.caption("Preferred response")
            st.write(context.answer_format)
            st.caption("Attempt")
            st.text(context.attempt)
        with st.container(border=True):
            st.subheader("See an answer take shape")
            st.write("Preview a fixed straight-line depreciation example with working notes.")
            is_sample_context = (
                context.level == "CA Intermediate"
                and context.subject == "Advanced Accounting"
                and context.chapter == MVP_CHAPTER
            )
            if st.button(
                "Preview a worked answer",
                key="worked_example",
                icon=":material/menu_book:",
                disabled=not is_sample_context,
                width="stretch",
            ):
                add_turn(SAMPLE_QUESTION, context, example=True)
                st.rerun()
            if not is_sample_context:
                st.caption("Select Intermediate → Advanced Accounting → depreciation to preview.")
            st.caption("Prepared example · no model or calculator")
        st.download_button(
            "Download chat",
            data=export_chat(st.session_state.messages, st.session_state.feedback),
            file_name="ca-chat-session.json",
            mime="application/json",
            disabled=not st.session_state.messages,
            icon=":material/download:",
            width="stretch",
            key="download_chat",
        )
        st.caption("Feedback is local and included in your chat download.")

    with main:
        st.subheader("A little clarity, one question at a time")
        configuration = load_app_settings()
        if configuration.api_enabled:
            st.info("AI enabled. Replies without sources are model explanations, not verified textbook answers.")
        else:
            st.info("Demo mode: no AI model is connected. Validated depreciation calculations and local document search still work.")
        if not st.session_state.messages:
            with st.container(border=True):
                st.markdown("#### Start with the question on your mind")
                st.write(
                    "Try the chat, choose an answer format, or preview the worked "
                    "example. Your study settings travel with each message."
                )
                st.caption(
                    "For a useful numerical question, include the figures, the required "
                    "output, and any assumptions."
                )
        for message in st.session_state.messages:
            render_message(message)

        question = st.chat_input(
            "Type a study question to try the interface…",
            max_chars=MAX_QUESTION_CHARS,
            key="question",
        )
        if question is not None:
            try:
                add_turn(question, context)
            except (ValueError, AppError) as error:
                st.error(str(error))
            else:
                st.rerun()


def library_tab(context, configuration, knowledge) -> None:
    render_library(context, configuration, knowledge)


def guide_tab() -> None:
    st.subheader("Your project, one phase at a time")
    st.write(
        "The workspace includes AI configuration, private PDF retrieval and validated depreciation tools. "
        "The course menu is a starter catalogue, not a verified ICAI syllabus."
    )
    st.markdown(
        "| Phase | Status | Includes |\n"
        "| --- | --- | --- |\n"
        "| 1 · Workspace | Implemented | Settings, demo chat, history and exports |\n"
        "| 2 · AI connection | Configuration required | Server-side provider adapter and error handling |\n"
        "| 3 · Knowledge base | Implemented | PDF ingestion, retrieval and citations |\n"
        "| 4 · Reliable calculations | Depreciation MVP | Decimal tools and numerical tests |\n"
        "| 5 · Deployment | Prepared; credentials required | Cloud secrets, access and hosting |\n"
        "| 6 · Evaluation | Local evaluation suite | At least 50 original questions and quality scores |\n"
        "| 7 · Optional fine-tuning | Pipeline only | Only if measured improvements justify it |\n"
        "| 8 · Expansion | Foundation controls | More subjects, accounts and production operations |"
    )
    st.caption("Change appearance using Streamlit's top-right menu → Settings → Theme.")
    with st.expander("Report an interface issue"):
        st.caption(
            "Describe what happened without private information. This creates a local "
            "download; it does not send a report to anyone."
        )
        with st.form("issue_form", clear_on_submit=True):
            description = st.text_area("What happened?", max_chars=1000)
            submitted = st.form_submit_button("Save issue locally")
        if submitted:
            cleaned = description.strip()
            if not cleaned:
                st.warning("Describe the issue before saving it.")
            elif len(cleaned) > 1000:
                st.warning("Keep the issue within 1,000 characters.")
            else:
                st.session_state.issues = (
                    st.session_state.issues
                    + [{"created_at": timestamp(), "description": cleaned, "phase": 1}]
                )[-10:]
                st.success("Issue saved in this session. Download it below.")
        if st.session_state.issues:
            st.download_button(
                "Download issue reports",
                json.dumps(st.session_state.issues, ensure_ascii=False, indent=2),
                file_name="ca-issue-phase1.json",
                mime="application/json",
            )


def main() -> None:
    try:
        configuration = load_app_settings()
        access_gate(configuration)
        provider, knowledge = runtime(configuration)
    except AppError as error:
        st.error(str(error))
        st.stop()
    initialize_session()
    context = sidebar()
    st.markdown(
        '<div class="ca-hero"><div class="ca-eyebrow">Learn with structure · Build understanding</div>'
        '<h1>Your CA study space.</h1>'
        '<p>A focused workspace for concepts, questions and clear working notes. '
        'Starting with CA Intermediate Advanced Accounting.</p></div>',
        unsafe_allow_html=True,
    )
    st.caption('Build a little consistency every day: 20 short questions, clear concepts, steady progress.')
    status, history, focus = st.columns(3)
    status.metric("Workspace", "CA tutor")
    history.metric("Questions in session", len(st.session_state.messages) // 2)
    focus.metric("AI connection", "Configured" if configuration.api_enabled else "Not connected")
    practice, tutor, library, calculator_tab, dataset_tab, guide = st.tabs(["Daily 20 marks", "Study chat", "Study library", "Calculations", "Datasets", "Project guide"])
    with practice:
        render_daily_practice()
    with tutor:
        tutor_tab(context)
    with library:
        library_tab(context, configuration, knowledge)
    with calculator_tab:
        render_calculator(context)
    with dataset_tab:
        render_dataset_status()
    with guide:
        guide_tab()
        with st.expander("Server API usage"):
            st.json(ledger().snapshot())
            st.caption("Conservative reservations include retry allowance; these are process-local estimates, not provider billing totals.")
    st.divider()
    st.caption("CA AI Assistant · Independent educational project · Not affiliated with ICAI")


if __name__ == "__main__":
    main()
