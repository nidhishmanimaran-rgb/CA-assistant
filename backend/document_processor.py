"""Page-aware extraction with explicit limits and an optional OCR adapter."""
from dataclasses import dataclass
from io import BytesIO
import re
from pypdf import PdfReader
from backend.errors import AppError


@dataclass(frozen=True)
class Page:
    number: int
    text: str
    ocr: bool = False


def extract_pdf(content: bytes, filename: str, *, authorized: bool, max_mb=10,
                max_pages=150, ocr=None) -> tuple[list[Page], list[str]]:
    if not authorized:
        raise AppError("Confirm you have permission to process this material.", "permission")
    if not filename.lower().endswith(".pdf") or not content.startswith(b"%PDF-"):
        raise AppError("Upload a readable PDF file.", "file_type")
    if not content or len(content) > max_mb * 1024 * 1024:
        raise AppError(f"The PDF must be no larger than {max_mb} MB.", "file_size")
    try:
        reader = PdfReader(BytesIO(content), strict=False)
        if reader.is_encrypted:
            raise AppError("Password-protected PDFs are not supported. Upload an authorized decrypted copy.", "encrypted_pdf")
        if not 0 < len(reader.pages) <= max_pages:
            raise AppError(f"Upload a PDF containing 1–{max_pages} pages.", "page_limit")
        pages, warnings, total = [], [], 0
        for index, page in enumerate(reader.pages):
            stream = page.get_contents()
            if stream and len(stream.get_data()) > 5_000_000:
                raise AppError("A PDF page is too complex to process safely.", "page_limit")
            text = page.extract_text(extraction_mode="layout") or ""
            used_ocr = False
            if len(text.strip()) < 30:
                if ocr is not None:
                    text = ocr(content, index)
                    used_ocr = True
                else:
                    warnings.append(f"Page {index + 1}: little readable text; optional OCR may be needed.")
            text = text.replace("\x00", "").replace("\r\n", "\n").strip()
            total += len(text)
            if len(text) > 100_000 or total > 2_000_000:
                raise AppError("Extracted text exceeds the document processing limit.", "text_limit")
            if text:
                pages.append(Page(index + 1, text, used_ocr))
        if not pages:
            raise AppError("No text could be extracted. Enable OCR for a scanned PDF.", "ocr_required")
        warnings.append("Review extracted figures and tables against the original PDF; extraction and OCR can lose mathematical layout.")
        return pages, warnings
    except AppError:
        raise
    except Exception:
        raise AppError("The PDF could not be read. Check that it is not damaged.", "invalid_pdf") from None


def ocr_page(content: bytes, page_index: int) -> str:
    try:
        import pypdfium2 as pdfium
        import pytesseract
        with pdfium.PdfDocument(content) as document:
            page = document[page_index]
            width, height = page.get_size()
            if width * height * 4 > 20_000_000:
                raise AppError("The scanned page exceeds the OCR pixel limit.", "ocr_limit")
            bitmap = page.render(scale=2)
            try:
                return pytesseract.image_to_string(bitmap.to_pil(), lang="eng", timeout=30)
            finally:
                bitmap.close()
                page.close()
    except AppError:
        raise
    except (ImportError, OSError):
        raise AppError("Install requirements-ocr.txt and the Tesseract executable to use OCR.", "ocr_unavailable") from None
    except Exception:
        raise AppError("OCR failed or timed out. Try a smaller, clearer PDF.", "ocr_failed") from None


def chunk_pages(pages: list[Page], target=1600, overlap=180) -> list[dict]:
    if target < 200 or not 0 <= overlap < target:
        raise ValueError("Invalid chunk parameters.")
    # Keep short adjacent questions/solutions together, including page crossings.
    text, spans = "", []
    for page in pages:
        start = len(text)
        text += page.text + "\n\n"
        spans.append((start, len(text), page.number))
    chunks, start = [], 0
    while start < len(text):
        end = min(start + target, len(text))
        if end < len(text):
            boundary = text.rfind("\n\n", start + target // 2, end)
            if boundary > start:
                end = boundary + 2
        snippet = text[start:end].strip()
        covered = [number for left, right, number in spans if left < end and right > start]
        if snippet:
            chunks.append({"text": snippet, "page_start": min(covered), "page_end": max(covered)})
        if end == len(text):
            break
        start = max(start + 1, end - overlap)
    if len(chunks) > 2000:
        raise AppError("The document produces too many searchable sections.", "chunk_limit")
    return chunks
