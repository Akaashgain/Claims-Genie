import json
import sqlite3
from pathlib import Path

import faiss
import fitz
import numpy as np

from embeddings.embedder import Embedder


BASE_DIR = Path(__file__).resolve().parents[1]
DOCUMENT_ROOT = BASE_DIR / "documents"
INDEX_DIR = BASE_DIR / "vectorstore" / "faiss_index"
INDEX_PATH = INDEX_DIR / "documents.index"
METADATA_PATH = INDEX_DIR / "metadata.json"
DB_PATH = BASE_DIR / "data" / "documents.sqlite3"
CHUNK_SIZE = 900
CHUNK_OVERLAP = 150


def _document_paths() -> list[tuple[str, Path]]:
    paths: list[tuple[str, Path]] = []
    for document_type in ("salary", "bank", "offer"):
        folder = DOCUMENT_ROOT / document_type
        folder.mkdir(parents=True, exist_ok=True)
        for path in sorted(folder.glob("*.pdf")):
            paths.append((document_type, path))
    return paths


def _chunk_text(text: str) -> list[str]:
    cleaned = " ".join(text.split())
    if not cleaned:
        return []

    chunks = []
    start = 0
    while start < len(cleaned):
        end = start + CHUNK_SIZE
        chunks.append(cleaned[start:end])
        start = max(end - CHUNK_OVERLAP, start + 1)
    return chunks


def _store_document_metadata(rows: list[dict]) -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            create table if not exists document_chunks (
                id integer primary key,
                document_type text not null,
                source text not null,
                page integer not null,
                chunk text not null
            )
            """
        )
        conn.execute("delete from document_chunks")
        conn.executemany(
            """
            insert into document_chunks (id, document_type, source, page, chunk)
            values (:id, :document_type, :source, :page, :chunk)
            """,
            rows,
        )
        conn.commit()


def build_faiss_index() -> dict:
    rows: list[dict] = []
    for document_type, path in _document_paths():
        with fitz.open(path) as pdf:
            for page_index, page in enumerate(pdf, start=1):
                for chunk in _chunk_text(page.get_text()):
                    rows.append(
                        {
                            "id": len(rows),
                            "document_type": document_type,
                            "source": path.name,
                            "page": page_index,
                            "chunk": chunk,
                        }
                    )

    if not rows:
        raise ValueError("No PDF documents found in documents/salary, documents/bank, or documents/offer.")

    embedder = Embedder()
    vectors = embedder.embed([row["chunk"] for row in rows])
    vectors = np.asarray(vectors, dtype="float32")
    faiss.normalize_L2(vectors)

    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)

    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(INDEX_PATH))
    METADATA_PATH.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    _store_document_metadata(rows)

    return {"documents": len({row["source"] for row in rows}), "chunks": len(rows)}


def _load_index_and_metadata():
    if not INDEX_PATH.exists() or not METADATA_PATH.exists():
        build_faiss_index()

    index = faiss.read_index(str(INDEX_PATH))
    metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    return index, metadata


def search_documents(question: str, document_type: str = "all", top_k: int = 5) -> list[dict]:
    index, metadata = _load_index_and_metadata()
    embedder = Embedder()
    query_vector = np.asarray(embedder.embed([question]), dtype="float32")
    faiss.normalize_L2(query_vector)

    search_k = min(max(top_k * 4, top_k), len(metadata))
    scores, ids = index.search(query_vector, search_k)

    matches: list[dict] = []
    for score, row_id in zip(scores[0], ids[0]):
        if row_id < 0:
            continue
        row = dict(metadata[row_id])
        if document_type != "all" and row["document_type"] != document_type:
            continue
        row["score"] = float(score)
        matches.append(row)
        if len(matches) >= top_k:
            break

    return matches
