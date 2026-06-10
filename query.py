"""Milestone 5 (core) — Grounded generation.

Retrieves the top-k chunks for a question (index.py) and asks a Groq-hosted LLM to
answer using ONLY those chunks. Grounding is enforced two ways:
  1. System prompt: answer only from the provided context; if it's not there, say so;
     do not use outside knowledge.
  2. Structural: only the retrieved chunks are placed in the prompt, and clearly
     off-topic queries (best retrieved distance above RELEVANCE_THRESHOLD) short-circuit
     to a refusal without calling the model.

Run as a CLI:
    python query.py "What's the best dorm for freshmen?"
"""

from __future__ import annotations

import json
import os
import sys

from dotenv import load_dotenv
from groq import Groq

from index import build_index, retrieve, TOP_K

load_dotenv()

GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# Cosine distance above which a retrieved chunk is treated as irrelevant. In-domain
# matches land ~0.35-0.6; off-domain questions sit well above this.
RELEVANCE_THRESHOLD = 0.85

REFUSAL = (
    "I don't have information on that in the UW guide documents. I can help with UW "
    "topics like dorms, dining, professors, registration, academic support, or "
    "visa/F-1 status."
)

SYSTEM_PROMPT = (
    "You are the Unofficial UW Guide, a question-answering assistant about the "
    "University of Washington (Seattle) for students.\n"
    "Answer the user's question using ONLY the numbered context passages provided. "
    "Do not use any outside knowledge or make assumptions beyond the context. "
    "Do not invent sources, names, or numbers. Be concise and practical.\n\n"
    "Respond with a JSON object with exactly two keys:\n"
    '  "answer": your answer as a string.\n'
    '  "answered_from_context": true if the context actually contained the answer, '
    "false otherwise.\n"
    "If the context does not contain the answer, set answered_from_context to false "
    f'and set answer to exactly: "{REFUSAL}"'
)


def _client() -> Groq:
    key = os.getenv("GROQ_API_KEY", "")
    if not key or key == "your_key_here":
        raise RuntimeError(
            "GROQ_API_KEY is not set. Copy .env.example to .env and add your key "
            "from https://console.groq.com"
        )
    return Groq(api_key=key)


def _format_context(results: list[dict]) -> str:
    blocks = []
    for r in results:
        label = r["source_label"] or r["source_file"]
        blocks.append(f"[{r['rank']}] (Source: {label})\n{r['text']}")
    return "\n\n".join(blocks)


def _unique_sources(results: list[dict]) -> list[dict]:
    """Deduplicate retrieved chunks down to one entry per source file."""
    seen: dict[str, dict] = {}
    for r in results:
        key = r["source_file"]
        if key not in seen:
            seen[key] = {"source_file": key, "source_label": r["source_label"]}
    return list(seen.values())


def answer(question: str, k: int = TOP_K, collection=None) -> dict:
    """Answer a question grounded in the retrieved chunks.

    Returns {answer, sources, retrieved}: `sources` is the deduped list of source files
    used as context; `retrieved` is the raw top-k result dicts (for the UI's source panel).
    """
    results = retrieve(question, k=k, collection=collection)
    relevant = [r for r in results if r["distance"] <= RELEVANCE_THRESHOLD]

    if not relevant:
        return {"answer": REFUSAL, "sources": [], "retrieved": results}

    completion = _client().chat.completions.create(
        model=GROQ_MODEL,
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Context passages:\n{_format_context(relevant)}\n\n"
                    f"Question: {question}"
                ),
            },
        ],
    )

    raw = completion.choices[0].message.content.strip()
    try:
        parsed = json.loads(raw)
        text = str(parsed.get("answer", "")).strip() or REFUSAL
        grounded = bool(parsed.get("answered_from_context", False))
    except (json.JSONDecodeError, AttributeError):
        # Fall back gracefully if the model didn't return valid JSON.
        text, grounded = raw, True

    return {
        "answer": text,
        # Only attribute sources when the model actually answered from the context.
        "sources": _unique_sources(relevant) if grounded else [],
        "retrieved": results,
    }


def main() -> None:
    if len(sys.argv) < 2:
        print('Usage: python query.py "your question"')
        raise SystemExit(1)

    question = " ".join(sys.argv[1:])
    # Ensure the index exists (builds on first run, reused afterward).
    collection = build_index()
    result = answer(question, collection=collection)

    print("\nAnswer:")
    print(result["answer"])
    print("\nSources:")
    if result["sources"]:
        for s in result["sources"]:
            label = s["source_label"] or s["source_file"]
            print(f"  - {label} ({s['source_file']})")
    else:
        print("  (none relevant)")


if __name__ == "__main__":
    main()
