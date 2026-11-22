from dataclasses import replace
from io import BytesIO
import pytest
from pypdf import PdfWriter
from backend.document_processor import extract_pdf, chunk_pages
from backend.errors import AppError
from backend.embeddings import LocalEmbeddings
from backend.retrieval import KnowledgeBase
from backend.syllabus_versions import applicable


def test_extract_preserves_numbers_and_page_numbers(pdf_bytes):
    pages, warnings = extract_pdf(pdf_bytes(
        "Cost 850000\nResidual 50000\nUseful life 8 years",
        "Annual depreciation = (850000 - 50000) / 8 = 100000"
    ), "chapter.pdf", authorized=True)
    assert [page.number for page in pages] == [1, 2]
    assert "850000" in pages[0].text and "100000" in pages[1].text
    assert warnings


def test_permission_type_size_and_encryption(pdf_bytes):
    content = pdf_bytes("Original, independently authored accounting note.")
    for payload, name, kwargs in [
        (content, "a.pdf", {"authorized": False}),
        (b"not a PDF", "a.pdf", {"authorized": True}),
        (content, "a.exe", {"authorized": True}),
        (content, "a.pdf", {"authorized": True, "max_mb": 0}),
    ]:
        with pytest.raises(AppError):
            extract_pdf(payload, name, **kwargs)
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.encrypt("private")
    output = BytesIO()
    writer.write(output)
    with pytest.raises(AppError, match="Password"):
        extract_pdf(output.getvalue(), "locked.pdf", authorized=True)


def test_scanned_pdf_uses_optional_ocr_callback():
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    output = BytesIO()
    writer.write(output)
    with pytest.raises(AppError, match="OCR"):
        extract_pdf(output.getvalue(), "scan.pdf", authorized=True)
    pages, _ = extract_pdf(output.getvalue(), "scan.pdf", authorized=True,
                           ocr=lambda content, index: "Original OCR text with cost 850000 and residual 50000.")
    assert pages[0].ocr and pages[0].number == 1


def test_chunks_keep_page_ranges(pdf_bytes):
    pages, _ = extract_pdf(pdf_bytes("Question: Cost 100000, life 5 years.",
                                    "Solution: For zero residual, annual charge is 20000."),
                           "note.pdf", authorized=True)
    chunks = chunk_pages(pages)
    assert chunks[0]["page_start"] == 1 and chunks[0]["page_end"] == 2
    assert "Question:" in chunks[0]["text"] and "Solution:" in chunks[0]["text"]


def test_persistent_retrieval_scope_replacement_and_deletion(tmp_path, pdf_bytes, metadata, context):
    database = tmp_path / "kb.sqlite"
    kb = KnowledgeBase(database, "a" * 32, LocalEmbeddings())
    content = pdf_bytes("Straight-line depreciation spreads cost less residual value over useful life.")
    result = kb.ingest(content, "../../private.pdf", metadata, authorized=True)
    reloaded = KnowledgeBase(database, "a" * 32, LocalEmbeddings())
    hits = reloaded.search("straight-line depreciation cost residual", context)
    assert hits and hits[0]["metadata"]["title"] == metadata.title
    assert not reloaded.search("depreciation", replace(context, attempt="Different attempt"))
    assert not KnowledgeBase(database, "b" * 32, LocalEmbeddings()).search("depreciation", context)
    with pytest.raises(AppError):
        kb.ingest(b"broken", "bad.pdf", metadata, authorized=True, replace_id=result["id"])
    assert len(kb.list_documents()) == 1
    updated = kb.ingest(content, "new.pdf", replace(metadata, version="2"), authorized=True, replace_id=result["id"])
    assert len(kb.list_documents()) == 1 and updated["id"] != result["id"]
    assert not KnowledgeBase(database, "b" * 32, LocalEmbeddings()).delete(updated["id"])
    assert kb.delete(updated["id"])
    assert not kb.search("depreciation", context)


def test_statutory_metadata_never_crosses_years_or_dates(metadata, context):
    legal = replace(metadata, subject="Taxation", assessment_year="2027-28", effective_from="2026-04-01")
    legal.validate()
    selected = replace(context, subject="Taxation", assessment_year="2027-28", as_of="2026-11-22")
    assert applicable(legal, selected)
    assert not applicable(legal, replace(selected, assessment_year="2026-27"))
    assert not applicable(legal, replace(selected, as_of="2025-11-22"))
    assert not applicable(legal, replace(selected, as_of=""))
    with pytest.raises(AppError):
        replace(legal, timeless=True).validate()


def test_invalid_workspace_identifier_cannot_be_a_path(tmp_path):
    with pytest.raises(AppError):
        KnowledgeBase(tmp_path / "kb.sqlite", "../other", LocalEmbeddings())
