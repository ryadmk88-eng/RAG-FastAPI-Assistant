import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer


CHUNKS_FILE = Path("data/fastapi_chunks.json")
EMBEDDINGS_FILE = Path("data/fastapi_embeddings.npy")

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def main():
    if not CHUNKS_FILE.exists():
        print("ERROR: data/fastapi_chunks.json was not found.")
        return

    print("Loading chunks...")

    with CHUNKS_FILE.open("r", encoding="utf-8") as file:
        chunks = json.load(file)

    print(f"Loaded {len(chunks)} chunks.")

    # Include useful context in each embedding
    texts = []

    for chunk in chunks:
        text_for_embedding = (
            f"Title: {chunk['title']}\n"
            f"Heading: {chunk['heading']}\n"
            f"{chunk['text']}"
        )

        texts.append(text_for_embedding)

    print(f"Loading embedding model: {MODEL_NAME}")

    model = SentenceTransformer(MODEL_NAME)

    print("Creating embeddings...")

    embeddings = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=True,
        normalize_embeddings=True,
    )

    np.save(EMBEDDINGS_FILE, embeddings)

    print()
    print("Embedding generation finished.")
    print(f"Created embeddings for {len(chunks)} chunks.")
    print(f"Embedding dimensions: {embeddings.shape[1]}")
    print(f"Output: {EMBEDDINGS_FILE}")


if __name__ == "__main__":
    main()