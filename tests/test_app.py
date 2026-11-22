from pathlib import Path

from streamlit.testing.v1 import AppTest

from config.catalog import ANSWER_FORMATS, MVP_CHAPTER

APP = Path(__file__).resolve().parents[1] / "app.py"


def start_app():
    app = AppTest.from_file(str(APP), default_timeout=20).run()
    assert not app.exception
    return app


def test_startup_without_api_keys(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    app = start_app()
    assert app.selectbox(key="level").value == "CA Intermediate"
    assert app.selectbox(key="chapter").value == MVP_CHAPTER
    assert app.session_state["messages"] == []
    assert app.get("file_uploader")[0].disabled


def test_chat_survives_rerun_and_preserves_original_context():
    app = start_app()
    app.text_input(key="attempt").set_value("My original attempt").run()
    app.chat_input(key="question").set_value("Can you explain depreciation?").run()
    assert not app.exception
    assert len(app.session_state["messages"]) == 2
    assert "no AI model is connected" in app.session_state["messages"][1]["content"]
    app.text_input(key="attempt").set_value("My new attempt").run()
    assert app.session_state["messages"][0]["context"]["attempt"] == "My original attempt"
    app.chat_input(key="question").set_value("A follow-up question").run()
    assert len(app.session_state["messages"]) == 4
    assert app.session_state["messages"][2]["context"]["attempt"] == "My new attempt"


def test_level_and_subject_changes_reset_dependent_controls():
    app = start_app()
    app.selectbox(key="subject").set_value("Taxation").run()
    assert not app.exception
    assert app.selectbox(key="chapter").value == "Income-tax overview"
    assert app.button(key="worked_example").disabled
    app.selectbox(key="level").set_value("CA Final").run()
    assert not app.exception
    assert app.selectbox(key="subject").value == "Financial Reporting"
    app.selectbox(key="level").set_value("CA Intermediate").run()
    assert not app.exception
    assert app.selectbox(key="subject").value == "Advanced Accounting"
    assert app.selectbox(key="chapter").value == MVP_CHAPTER


def test_answer_formats_and_explicit_example():
    app = start_app()
    for answer_format in ANSWER_FORMATS:
        app.selectbox(key="answer_format").set_value(answer_format).run()
        app.button(key="worked_example").click().run()
        assert not app.exception
        answer = app.session_state["messages"][-1]
        assert answer["kind"] == "prepared_example"
        assert answer["context"]["answer_format"] == answer_format
        assert "Prepared example" in answer["content"]
    app.chat_input(key="question").set_value("Now change the cost to ₹9,00,000").run()
    assert "₹1,00,000" not in app.session_state["messages"][-1]["content"]


def test_clear_and_separate_sessions():
    first = start_app()
    first.chat_input(key="question").set_value("Private session question").run()
    second = start_app()
    assert second.session_state["messages"] == []
    first.button(key="clear_chat").click().run()
    assert not first.exception
    assert first.session_state["messages"] == []
    assert first.session_state["feedback"] == {}


def test_user_text_is_not_rendered_as_html():
    app = start_app()
    question = '<script>alert("test")</script> ![image](https://example.com/track)'
    app.chat_input(key="question").set_value(question).run()
    assert not app.exception
    assert question in [element.value for element in app.text]
    assert app.session_state["messages"][0]["content"] == question


def test_issue_reporting_requires_description():
    app = start_app()
    submit = next(button for button in app.button if button.label == "Save issue locally")
    submit.click().run()
    assert app.session_state["issues"] == []
    app.text_area[0].set_value("The layout needs attention on my screen.")
    next(button for button in app.button if button.label == "Save issue locally").click().run()
    assert not app.exception
    assert len(app.session_state["issues"]) == 1


def test_daily_quiz_screen_is_visible():
    app = start_app()
    assert any("Daily 20 marks" in tab.label for tab in app.get("tab"))
    assert any("Your daily 20-minute practice" in element.value for element in app.get("subheader"))
