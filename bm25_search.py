import json
import re
from pathlib import Path

from rank_bm25 import BM25Okapi


CHUNKS_FILE = Path("data/fastapi_chunks.json")
TOP_K = 5


def tokenize(text):
    """
    Simple tokenizer for BM25.
    Lowercases text and keeps words/numbers.
    """
    return re.findall(r"\b\w+\b", text.lower())


def load_chunks():
    with CHUNKS_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def build_bm25(chunks):
    corpus = []

    for chunk in chunks:
        searchable_text = (
            f"{chunk['title']} "
            f"{chunk['heading']} "
            f"{chunk['text']}"
        )

        corpus.append(
            tokenize(searchable_text)
        )

    return BM25Okapi(corpus)


def bm25_search(query, bm25, chunks, top_k=TOP_K):
    query_tokens = tokenize(query)

    scores = bm25.get_scores(query_tokens)

    best_indices = sorted(
        range(len(scores)),
        key=lambda index: scores[index],
        reverse=True
    )[:top_k]

    results = []

    for index in best_indices:
        chunk = chunks[index]

        results.append(
            {
                "score": float(scores[index]),
                "chunk_id": chunk["chunk_id"],
                "title": chunk["title"],
                "heading": chunk["heading"],
                "url": chunk["url"],
                "text": chunk["text"],
            }
        )

    return results


def main():
    if not CHUNKS_FILE.exists():
        print("ERROR: data/fastapi_chunks.json was not found.")
        return

    print("Loading FastAPI chunks...")

    chunks = load_chunks()

    print(f"Loaded {len(chunks)} chunks.")

    print("Building BM25 index...")

    bm25 = build_bm25(chunks)

    print()
    print("BM25 search is ready.")
    print("Type 'exit' to stop.")
    print()

    while True:
        query = input("Ask a FastAPI question: ").strip()

        if query.lower() == "exit":
            break

        if not query:
            continue

        results = bm25_search(
            query,
            bm25,
            chunks
        )

        print()
        print("=" * 80)

        for number, result in enumerate(results, start=1):
            print(f"\nResult {number}")
            print(f"Score: {result['score']:.4f}")
            print(f"Title: {result['title']}")
            print(f"Heading: {result['heading']}")
            print(f"URL: {result['url']}")
            print()
            print(result["text"][:700])
            print()

        print("=" * 80)
        print()


if __name__ == "__main__":
    main()