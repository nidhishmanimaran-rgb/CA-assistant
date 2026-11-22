"""Persistent vectors in SQLite; FAISS ranks only records in the authorized scope."""
from contextlib import contextmanager
from dataclasses import asdict
import hashlib
import math
import json
from pathlib import Path
import re
import sqlite3
from uuid import uuid4

from backend.document_processor import chunk_pages, extract_pdf
from backend.embeddings import validate_vectors
from backend.errors import AppError
from backend.syllabus_versions import DocumentMeta, applicable


class KnowledgeBase:
    def __init__(self, database: Path, tenant: str, embedder):
        if not re.fullmatch(r"[a-f0-9]{32,64}", tenant):
            raise AppError("Invalid workspace identifier.", "workspace")
        self.database, self.tenant, self.embedder = Path(database), tenant, embedder
        self.last_engine = "not_used"

    @contextmanager
    def connection(self):
        self.database.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.database, timeout=10)
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("""CREATE TABLE IF NOT EXISTS documents(
            id TEXT PRIMARY KEY, tenant TEXT NOT NULL, metadata TEXT NOT NULL,
            fingerprint TEXT NOT NULL, embedding_model TEXT NOT NULL)""")
        connection.execute("""CREATE TABLE IF NOT EXISTS chunks(
            id INTEGER PRIMARY KEY, document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
            content TEXT NOT NULL, page_start INTEGER NOT NULL, page_end INTEGER NOT NULL, vector TEXT NOT NULL)""")
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def list_documents(self):
        if not self.database.exists():
            return []
        with self.connection() as db:
            return [{"id": row[0], **json.loads(row[1]), "embedding_model": row[2]} for row in db.execute(
                "SELECT id, metadata, embedding_model FROM documents WHERE tenant=? ORDER BY rowid DESC", (self.tenant,)
            )]

    def ingest(self, content, filename, metadata: DocumentMeta, *, authorized, replace_id=None, ocr=None, settings=None):
        metadata.validate()
        pages, warnings = extract_pdf(
            content, filename, authorized=authorized, ocr=ocr,
            max_mb=settings.max_upload_mb if settings else 10,
            max_pages=settings.max_pdf_pages if settings else 150,
        )
        documents = self.list_documents()
        if replace_id and replace_id not in {item["id"] for item in documents}:
            raise AppError("The document to replace is not in this workspace.", "workspace")
        if not replace_id and any(
            all(item.get(key) == getattr(metadata, key) for key in ("title", "level", "subject", "chapter", "attempt"))
            for item in documents
        ):
            raise AppError("This title and scope already exist. Use Replace to avoid mixing editions.", "duplicate_document")
        if not replace_id and len(documents) >= 20:
            raise AppError("This workspace is limited to 20 documents. Remove an older document first.", "document_limit")
        chunks = chunk_pages(pages)
        vectors = validate_vectors(self.embedder.encode([chunk["text"] for chunk in chunks]), len(chunks))
        document_id = uuid4().hex
        with self.connection() as db:
            # Replacement is atomic; extraction/embedding failures preserve the old version.
            if replace_id:
                db.execute("DELETE FROM documents WHERE id=? AND tenant=?", (replace_id, self.tenant))
            db.execute("INSERT INTO documents VALUES(?,?,?,?,?)", (
                document_id, self.tenant, json.dumps(asdict(metadata), ensure_ascii=False),
                hashlib.sha256(content).hexdigest(), self.embedder.identifier,
            ))
            db.executemany("INSERT INTO chunks(document_id,content,page_start,page_end,vector) VALUES(?,?,?,?,?)", [
                (document_id, chunk["text"], chunk["page_start"], chunk["page_end"], json.dumps(vector))
                for chunk, vector in zip(chunks, vectors)
            ])
        return {"id": document_id, "pages": len(pages), "chunks": len(chunks), "warnings": warnings}

    def delete(self, document_id):
        if not self.database.exists():
            return False
        with self.connection() as db:
            return db.execute("DELETE FROM documents WHERE id=? AND tenant=?", (document_id, self.tenant)).rowcount > 0

    def search(self, question, context, top_k=4, min_score=0.12):
        if not self.database.exists():
            return []
        with self.connection() as db:
            candidates = []
            for doc_id, metadata, embedding_model in db.execute(
                "SELECT id,metadata,embedding_model FROM documents WHERE tenant=?", (self.tenant,)
            ):
                meta = DocumentMeta(**json.loads(metadata))
                if embedding_model != self.embedder.identifier or not applicable(meta, context):
                    continue
                for content, start, end, vector in db.execute(
                    "SELECT content,page_start,page_end,vector FROM chunks WHERE document_id=?", (doc_id,)
                ):
                    if len(candidates) >= 5000:
                        raise AppError("The matching collection exceeds 5,000 sections.", "retrieval_limit")
                    candidates.append({"document_id": doc_id, "text": content, "page_start": start,
                                       "page_end": end, "metadata": asdict(meta), "vector": json.loads(vector)})
        if not candidates:
            return []
        if len(candidates) > 40_000:
            raise AppError("This collection exceeds the local retrieval limit.", "retrieval_limit")
        try:
            import faiss
            import numpy as np
            self.last_engine = "faiss"
            vectors = np.asarray([item["vector"] for item in candidates], dtype="float32")
            query = np.asarray(validate_vectors(self.embedder.encode([question]), 1), dtype="float32")
            if vectors.shape[1] != query.shape[1]:
                raise AppError("Embedding dimensions changed; reindex these documents.", "embedding")
            faiss.normalize_L2(vectors)
            faiss.normalize_L2(query)
            index = faiss.IndexFlatIP(vectors.shape[1])
            index.add(vectors)
            scores, indices = index.search(query, min(top_k, len(candidates)))
            result = []
            for score, position in zip(scores[0], indices[0]):
                if position >= 0 and float(score) >= min_score:
                    item = {key: value for key, value in candidates[int(position)].items() if key != "vector"}
                    result.append({**item, "source_id": f"S{len(result) + 1}", "score": float(score)})
            return result
        except AppError:
            raise
        except (ImportError, OSError):
            # Do not alter platform security controls or hide native-library failures.
            self.last_engine = "python_cosine_fallback"
            query = validate_vectors(self.embedder.encode([question]), 1)[0]
            qnorm = math.sqrt(sum(value * value for value in query)) or 1
            ranked = []
            for item in candidates:
                vector = item["vector"]
                if len(vector) != len(query):
                    raise AppError("Embedding dimensions changed; reindex these documents.", "embedding")
                norm = math.sqrt(sum(value * value for value in vector)) or 1
                score = sum(left * right for left, right in zip(vector, query)) / (norm * qnorm)
                ranked.append((score, item))
            results = []
            for score, item in sorted(ranked, key=lambda pair: pair[0], reverse=True)[:top_k]:
                if score >= min_score:
                    results.append({**{key: value for key, value in item.items() if key != "vector"},
                                    "source_id": f"S{len(results) + 1}", "score": score,
                                    "search_engine": self.last_engine})
            return results
