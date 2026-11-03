import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer


CHUNKS_FILE = Path("data/fastapi_chunks.json")
EMBEDDINGS_FILE = Path("data/fastapi_embeddings.npy")

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

TOP_K = 5


def load_data():
    with CHUNKS_FILE.open("r", encoding="utf-8") as file:
        chunks = json.load(file)

    embeddings = np.load(EMBEDDINGS_FILE)

    return chunks, embeddings


def semantic_search(query, model, chunks, embeddings, top_k=TOP_K):
    query_embedding = model.encode(
        query,
        normalize_embeddings=True
    )

    scores = embeddings @ query_embedding

    best_indices = np.argsort(scores)[::-1][:top_k]

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

    if not EMBEDDINGS_FILE.exists():
        print("ERROR: data/fastapi_embeddings.npy was not found.")
        return

    print("Loading FastAPI chunks and embeddings...")

    chunks, embeddings = load_data()

    print(f"Loaded {len(chunks)} chunks.")
    print(f"Loaded embeddings with shape: {embeddings.shape}")

    print(f"Loading model: {MODEL_NAME}")

    model = SentenceTransformer(MODEL_NAME)

    print()
    print("Semantic search is ready.")
    print("Type 'exit' to stop.")
    print()

    while True:
        query = input("Ask a FastAPI question: ").strip()

        if query.lower() == "exit":
            break

        if not query:
            continue

        results = semantic_search(
            query,
            model,
            chunks,
            embeddings
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