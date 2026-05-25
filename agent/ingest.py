"""
One-time ingestion: OCR the PDF, chunk, embed, build FAISS + BM25 index.
Run: python ingest.py
Output: storage/ directory -- commit to repo.
Runtime: ~20 min OCR + ~5 min embeddings.
"""
import json
import os
import re
from pathlib import Path

import pytesseract
from pdf2image import convert_from_path, pdfinfo_from_path
from dotenv import load_dotenv

from llama_index.core import Document, VectorStoreIndex, StorageContext, Settings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.faiss import FaissVectorStore
import faiss

load_dotenv()

PDF_PATH = Path("arnold_encyclopedia.pdf")
STORAGE_DIR = Path("storage")
CHUNK_SIZE = 512
CHUNK_OVERLAP = 64

# Approximate chapter start pages from the book's TOC.
_CHAPTER_MAP = [
    (1,   1, "Introduction to Bodybuilding"),
    (40,  2, "Chest Exercises"),
    (90,  2, "Back Exercises"),
    (140, 2, "Shoulder Exercises"),
    (190, 2, "Arm Exercises Biceps"),
    (220, 2, "Arm Exercises Triceps"),
    (250, 2, "Forearm Exercises"),
    (270, 2, "Leg Exercises"),
    (330, 2, "Calf Exercises"),
    (360, 2, "Abdominal Exercises"),
    (390, 3, "Training Programs"),
    (500, 4, "Competition"),
    (620, 5, "Health Nutrition and Diet"),
]

# Matches ALL-CAPS lines with at least two words (exercise headings)
_HEADING_RE = re.compile(r"^([A-Z][A-Z\s\-]{4,}[A-Z])\s*$", re.MULTILINE)


def _get_chapter(page_num: int) -> tuple:
    result = (1, "Introduction to Bodybuilding")
    for start, book, name in _CHAPTER_MAP:
        if page_num >= start:
            result = (book, name)
    return result


def _extract_exercise_name(text: str) -> str:
    match = _HEADING_RE.search(text)
    if match and len(match.group(1).split()) >= 2:
        return match.group(1).strip()
    return ""


def ocr_pdf(pdf_path: Path) -> list:
    print("Reading PDF metadata...")
    info = pdfinfo_from_path(str(pdf_path))
    total_pages = info["Pages"]

    print(f"OCR-ing {total_pages} pages page-by-page to conserve memory...")
    pages = []
    for i in range(1, total_pages + 1):
        if i % 50 == 0 or i == 1:
            print(f"  Page {i}/{total_pages}...")
        images = convert_from_path(str(pdf_path), dpi=200, first_page=i, last_page=i)
        if images:
            text = pytesseract.image_to_string(images[0], config="--psm 6")
            pages.append((i, text))
    return pages


def validate_headings(documents: list, n: int = 10) -> None:
    print(f"\n--- OCR Validation: first {n} detected exercise headings ---")
    found = 0
    for doc in documents:
        name = doc.metadata.get("exercise_name", "")
        if name and found < n:
            print(f"  [{doc.metadata['chapter']}] {name}")
            found += 1
        if found >= n:
            break
    if found == 0:
        print("  WARNING: No headings detected. Check OCR quality.")
        print("  -> Try dpi=300, or use AWS Textract as fallback.")
    else:
        print("  Check for digit substitutions: 1 for l, 5 for S, 0 for O.")
        print("  If corrupted, re-run with dpi=300 or use AWS Textract.")
    print("--- End validation ---\n")


def build_index(documents: list) -> None:
    STORAGE_DIR.mkdir(exist_ok=True)

    splitter = SentenceSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    nodes = splitter.get_nodes_from_documents(documents)
    print(f"Split into {len(nodes)} chunks from {len(documents)} pages")

    Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
    faiss_index = faiss.IndexFlatL2(1536)
    vector_store = FaissVectorStore(faiss_index=faiss_index)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    print("Embedding via OpenAI (text-embedding-3-small)...")
    index = VectorStoreIndex(nodes, storage_context=storage_context)
    index.storage_context.persist(persist_dir=str(STORAGE_DIR))
    print(f"FAISS index persisted to {STORAGE_DIR}/")

    # Save node text + metadata as JSON for BM25 reconstruction at load time.
    # JSON is used (not pickle) so the data is human-readable and auditable.
    node_data = [
        {"text": n.get_content(), "metadata": n.metadata}
        for n in nodes
    ]
    nodes_path = STORAGE_DIR / "nodes.json"
    with open(nodes_path, "w", encoding="utf-8") as f:
        json.dump(node_data, f, ensure_ascii=False)
    print(f"Node data saved to {nodes_path} ({len(node_data)} nodes)")


def main() -> None:
    pages = ocr_pdf(PDF_PATH)

    documents = []
    for page_num, text in pages:
        if not text.strip():
            continue
        book_num, chapter = _get_chapter(page_num)
        doc = Document(
            text=text,
            metadata={
                "page": page_num,
                "book": book_num,
                "chapter": chapter,
                "exercise_name": _extract_exercise_name(text),
            },
        )
        documents.append(doc)

    validate_headings(documents)
    build_index(documents)
    print("Done. Commit the storage/ directory.")


if __name__ == "__main__":
    main()
