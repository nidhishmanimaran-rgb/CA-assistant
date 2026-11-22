from io import BytesIO
import pytest
from backend.session import StudyContext
from backend.syllabus_versions import DocumentMeta
from config.catalog import MVP_CHAPTER


@pytest.fixture(autouse=True)
def offline_defaults(monkeypatch, tmp_path):
    for key, value in {"LLM_PROVIDER": "demo", "ALLOW_PAID_API": "false",
                       "EMBEDDING_BACKEND": "local", "REQUIRE_PASSWORD": "false",
                       "DATA_DIR": str(tmp_path / "data")}.items():
        monkeypatch.setenv(key, value)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)


@pytest.fixture
def context():
    return StudyContext("CA Intermediate", "Advanced Accounting", MVP_CHAPTER,
                        "May 2027", "English", "Detailed solution")


@pytest.fixture
def metadata(context):
    return DocumentMeta("Original depreciation notes", context.level, context.subject,
                        context.chapter, context.attempt, "1", "2026-11-21")


@pytest.fixture
def pdf_bytes():
    def build(*pages):
        from reportlab.pdfgen import canvas
        output = BytesIO()
        document = canvas.Canvas(output)
        for content in pages:
            text = document.beginText(50, 780)
            for line in content.splitlines():
                text.textLine(line)
            document.drawText(text)
            document.showPage()
        document.save()
        return output.getvalue()
    return build
