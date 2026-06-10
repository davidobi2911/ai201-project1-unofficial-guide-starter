"""Milestone 4 — Embedding and retrieval.

Embeds the chunks from ingest.py with the all-MiniLM-L6-v2 sentence-transformer,
stores them in a persistent ChromaDB collection, and retrieves the top-k most
relevant chunks for a query (cosine similarity).

Embedding model: all-MiniLM-L6-v2 (local, no API key) — small, fast, and strong on
short semantic-similarity text like reviews and tips, which fits this corpus.
Top-k: 5 (see planning.md).

Run directly to build the index and try a couple of sample queries:
    python index.py
The collection is persisted in ./chroma_db, so later runs skip re-embedding.
"""

from __future__ import annotations

import os

import chromadb
from chromadb.utils import embedding_functions

from ingest import chunk_documents

MODEL_NAME = "all-MiniLM-L6-v2"
COLLECTION_NAME = "uw_guide"
CHROMA_DIR = os.path.join(os.path.dirname(__file__), "chroma_db")
TOP_K = 5


def _embedding_function():
    return embedding_functions.SentenceTransformerEmbeddingFunction(model_name=MODEL_NAME)


def build_index(rebuild: bool = False) -> chromadb.api.models.Collection.Collection:
    """Embed all chunks into a persistent ChromaDB collection.

    Idempotent: if the collection already holds exactly the current number of chunks
    (and rebuild is False), it's reused as-is instead of re-embedding.
    """
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    ef = _embedding_function()
    chunks = chunk_documents()

    try:
        existing = client.get_collection(COLLECTION_NAME, embedding_function=ef)
    except Exception:
        existing = None

    if existing is not None and not rebuild and existing.count() == len(chunks):
        print(f"Collection '{COLLECTION_NAME}' already has {existing.count()} embeddings.")
        return existing

    # (Re)build from scratch so stale or partial state can't linger.
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )

    print(f"Embedding {len(chunks)} chunks with {MODEL_NAME}...")
    collection.add(
        ids=[c.id for c in chunks],
        documents=[c.text for c in chunks],
        metadatas=[
            {
                "source_file": c.source_file,
                "source_label": c.source_label,
                "chunk_index": c.chunk_index,
            }
            for c in chunks
        ],
    )
    print(f"Done. Collection has {collection.count()} embeddings.")
    return collection


def retrieve(query: str, k: int = TOP_K, collection=None) -> list[dict]:
    """Return the top-k chunks for a query as a list of result dicts.

    Each dict: {rank, id, text, source_file, source_label, distance}.
    Lower distance = more similar (cosine distance).
    """
    if collection is None:
        collection = build_index()

    res = collection.query(query_texts=[query], n_results=k)
    results: list[dict] = []
    for i in range(len(res["ids"][0])):
        meta = res["metadatas"][0][i]
        results.append(
            {
                "rank": i + 1,
                "id": res["ids"][0][i],
                "text": res["documents"][0][i],
                "source_file": meta.get("source_file", ""),
                "source_label": meta.get("source_label", ""),
                "distance": res["distances"][0][i],
            }
        )
    return results


def _print_results(query: str, results: list[dict]) -> None:
    print(f'\nQuery: "{query}"')
    print("----")
    for r in results:
        snippet = " ".join(r["text"].split())
        if len(snippet) > 100:
            snippet = snippet[:100].rstrip() + "..."
        print(f'[{r["rank"]}] {r["source_file"]} (dist: {r["distance"]:.2f})')
        print(f'    "{snippet}"')


def main() -> None:
    collection = build_index()
    for query in [
        "What do students say about Stuart Reges?",
        "What's the best dorm for freshmen?",
        "How do I keep my F-1 visa status?",
    ]:
        _print_results(query, retrieve(query, collection=collection))


if __name__ == "__main__":
    main()
