import json
import os
from pathlib import Path
from typing import Optional

import bm25s
from dotenv import load_dotenv
from llama_index.core import StorageContext, load_index_from_storage, Settings
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.faiss import FaissVectorStore

load_dotenv()

STORAGE_DIR = Path(__file__).parent / "storage"

_state: Optional[dict] = None


def load_retriever() -> dict:
    """Load FAISS + BM25 index from storage/. Cached after first call."""
    global _state
    if _state is not None:
        return _state

    Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
    vector_store = FaissVectorStore.from_persist_dir(str(STORAGE_DIR))
    storage_context = StorageContext.from_defaults(
        vector_store=vector_store,
        persist_dir=str(STORAGE_DIR),
    )
    index = load_index_from_storage(storage_context)
    vector_retriever = index.as_retriever(similarity_top_k=4)

    with open(STORAGE_DIR / "nodes.json", encoding="utf-8") as f:
        node_data: list = json.load(f)

    corpus_texts = [d["text"] for d in node_data if "text" in d]
    bm25_index = bm25s.BM25()
    bm25_index.index(bm25s.tokenize(corpus_texts))

    _state = {
        "vector_retriever": vector_retriever,
        "bm25_index": bm25_index,
        "corpus_texts": corpus_texts,
    }
    return _state


def retrieve(state: dict, query: str) -> list:
    """Hybrid FAISS + BM25 retrieval. Returns up to 5 deduplicated text passages."""
    if not query or not query.strip():
        return []

    vector_retriever = state["vector_retriever"]
    bm25_index = state["bm25_index"]
    corpus_texts = state["corpus_texts"]

    faiss_texts = [n.node.get_content() for n in vector_retriever.retrieve(query)]

    try:
        tokenized_query = bm25s.tokenize([query])
        scores, idxs = bm25_index.retrieve(tokenized_query, k=3)
        bm25_texts = [corpus_texts[int(i)] for i in idxs[0]]
    except (IndexError, ValueError, TypeError):
        bm25_texts = []

    seen: set = set()
    combined: list = []
    for text in faiss_texts + bm25_texts:
        key = text[:100]
        if key not in seen:
            seen.add(key)
            combined.append(text)

    return combined[:5]
