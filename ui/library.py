"""Authorized document ingestion and management for the current session's corpus."""
from datetime import datetime
from zoneinfo import ZoneInfo
import streamlit as st
from backend.document_processor import ocr_page
from backend.errors import AppError
from backend.syllabus_versions import DocumentMeta


def render_library(context, settings, knowledge):
    st.subheader("Your study library")
    st.write("Add material you are authorized to process. Its metadata must match the study context selected in the sidebar.")
    st.caption("Search mode: " + ("semantic embeddings" if knowledge.embedder.semantic else "local keyword vectors (offline baseline)"))
    authorized = st.checkbox("I have permission to use and process this material.", key="doc_authorized")
    upload = st.file_uploader("Upload a chapter PDF", type=["pdf"], disabled=not authorized,
                              max_upload_size=settings.max_upload_mb, key="future_pdf")
    title = st.text_input("Document title", max_chars=200, key="doc_title")
    version = st.text_input("Edition / source version", value="1", max_chars=100, key="doc_version")
    topic = st.text_input("Topic", max_chars=200, key="doc_topic")
    published = st.date_input("Publication / revision date",
                             value=datetime.now(ZoneInfo("Asia/Kolkata")).date(), key="doc_published")
    timeless = st.checkbox("This is a timeless conceptual note (not tax or law).", key="doc_timeless")
    effective_from = st.text_input("Effective from (YYYY-MM-DD, required for tax/law)", key="doc_effective_from")
    effective_to = st.text_input("Effective to (YYYY-MM-DD, optional)", key="doc_effective_to")
    use_ocr = st.checkbox("Use optional OCR for scanned pages", key="doc_ocr")
    st.caption("OCR requires requirements-ocr.txt and Tesseract. Always verify tables and numerical symbols.")
    documents = knowledge.list_documents()
    choices = {"Add as a new document": None, **{
        f"Replace: {item['title']} · {item['version']} · {item['id'][:6]}": item["id"] for item in documents
    }}
    choice = st.selectbox("Document action", tuple(choices), key="doc_action")
    external_ok = not knowledge.embedder.semantic or st.session_state.get("provider_consent", False)
    if knowledge.embedder.semantic:
        st.info("Semantic indexing sends extracted passages to OpenAI. Enable provider consent in the sidebar to continue.")
    if st.button("Process and index PDF", disabled=not (authorized and upload and external_ok), key="index_pdf"):
        try:
            metadata = DocumentMeta(
                title, context.level, context.subject, context.chapter,
                "*" if timeless else context.attempt, version, published.isoformat(), topic,
                context.assessment_year, context.fiscal_year, effective_from.strip(), effective_to.strip(), timeless,
            )
            with st.spinner("Reading pages and indexing passages…"):
                result = knowledge.ingest(
                    upload.getvalue(), upload.name, metadata, authorized=authorized,
                    replace_id=choices[choice], ocr=ocr_page if use_ocr else None, settings=settings,
                )
            st.success(f"Indexed {result['pages']} readable pages in {result['chunks']} sections.")
            for warning in result["warnings"]:
                st.warning(warning)
        except AppError as error:
            st.error(str(error))
    documents = knowledge.list_documents()
    if not documents:
        st.info("No documents have been uploaded or indexed in this session.")
    for item in documents:
        with st.expander(f"{item['title']} · version {item['version']}"):
            st.text(f"{item['level']} / {item['subject']} / {item['chapter']}\nAttempt: {item['attempt']}\nPublished: {item['publication_date']}")
            st.caption("Applicability metadata is supplied by the uploader, not verified by ICAI.")
            if st.button("Remove this document", key="delete_" + item["id"]):
                knowledge.delete(item["id"])
                st.rerun()
    st.caption("Original PDF bytes are not saved. Extracted text and vectors are private server data. This anonymous session owns its corpus; a refreshed session may lose access. Indexing is retrieval preparation, not model training.")
