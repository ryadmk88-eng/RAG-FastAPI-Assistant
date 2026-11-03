import json
import re
import time
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

from semantic_search import load_data, MODEL_NAME
from bm25_search import build_bm25


QUESTIONS_FILE = Path("evaluation_questions.json")
RESULTS_DIR = Path("results")
RESULTS_FILE = RESULTS_DIR / "retrieval_evaluation.json"

TOP_K = 5


def normalize_url(url):
    return url.rstrip("/")


def tokenize(text):
    return re.findall(r"\b\w+\b", text.lower())


def get_expected_urls(question):
    """
    Support both:
        "expected_url": "..."
    and:
        "expected_urls": ["...", "..."]
    """

    if "expected_urls" in question:
        urls = question["expected_urls"]
    elif "expected_url" in question:
        urls = [question["expected_url"]]
    else:
        raise ValueError(
            f"{question.get('id', 'Unknown question')} "
            "has no expected_url or expected_urls."
        )

    return [
        normalize_url(url)
        for url in urls
    ]


def evaluate_ranking(
    question,
    ranked_indices,
    chunks,
    response_time_ms,
):
    expected_urls = get_expected_urls(question)

    retrieved_urls = [
        chunks[index]["url"]
        for index in ranked_indices[:TOP_K]
    ]

    matched_rank = None
    matched_url = None

    for rank, retrieved_url in enumerate(
        retrieved_urls,
        start=1,
    ):
        normalized_retrieved = normalize_url(
            retrieved_url
        )

        if normalized_retrieved in expected_urls:
            matched_rank = rank
            matched_url = retrieved_url
            break

    return {
        "id": question["id"],
        "question": question["question"],
        "expected_urls": expected_urls,
        "matched_url": matched_url,
        "expected_rank": matched_rank,
        "hit_at_1": (
            matched_rank is not None
            and matched_rank <= 1
        ),
        "hit_at_3": (
            matched_rank is not None
            and matched_rank <= 3
        ),
        "hit_at_5": (
            matched_rank is not None
            and matched_rank <= 5
        ),
        "response_time_ms": round(
            response_time_ms,
            2,
        ),
        "retrieved_urls": retrieved_urls,
    }


def calculate_summary(results):
    total = len(results)

    if total == 0:
        return {
            "questions": 0,
            "hit_at_1": 0,
            "hit_at_3": 0,
            "hit_at_5": 0,
            "mean_reciprocal_rank": 0,
            "average_response_time_ms": 0,
        }

    hit_at_1 = sum(
        result["hit_at_1"]
        for result in results
    ) / total

    hit_at_3 = sum(
        result["hit_at_3"]
        for result in results
    ) / total

    hit_at_5 = sum(
        result["hit_at_5"]
        for result in results
    ) / total

    reciprocal_ranks = []

    for result in results:
        rank = result["expected_rank"]

        if rank is None:
            reciprocal_ranks.append(0)
        else:
            reciprocal_ranks.append(
                1 / rank
            )

    mrr = sum(
        reciprocal_ranks
    ) / total

    average_response_time = sum(
        result["response_time_ms"]
        for result in results
    ) / total

    return {
        "questions": total,
        "hit_at_1": round(hit_at_1, 3),
        "hit_at_3": round(hit_at_3, 3),
        "hit_at_5": round(hit_at_5, 3),
        "mean_reciprocal_rank": round(
            mrr,
            3,
        ),
        "average_response_time_ms": round(
            average_response_time,
            2,
        ),
    }


def evaluate_semantic(
    questions,
    chunks,
    embeddings,
    model,
):
    print()
    print("=" * 70)
    print("SEMANTIC RETRIEVAL")
    print("=" * 70)

    results = []

    for question in questions:
        query = question["question"]

        start_time = time.perf_counter()

        query_embedding = model.encode(
            query,
            normalize_embeddings=True,
        )

        scores = embeddings @ query_embedding

        ranked_indices = np.argsort(
            scores
        )[::-1][:TOP_K]

        elapsed_ms = (
            time.perf_counter() - start_time
        ) * 1000

        result = evaluate_ranking(
            question,
            ranked_indices,
            chunks,
            elapsed_ms,
        )

        results.append(result)

        rank_text = (
            result["expected_rank"]
            if result["expected_rank"]
            is not None
            else "Not found"
        )

        print(
            f"Semantic | "
            f"{question['id']} | "
            f"Rank: {rank_text} | "
            f"{elapsed_ms:.2f} ms"
        )

    return results


def evaluate_bm25(
    questions,
    chunks,
    bm25,
):
    print()
    print("=" * 70)
    print("BM25 RETRIEVAL")
    print("=" * 70)

    results = []

    for question in questions:
        query = question["question"]

        start_time = time.perf_counter()

        tokenized_query = tokenize(query)

        scores = bm25.get_scores(
            tokenized_query
        )

        ranked_indices = np.argsort(
            scores
        )[::-1][:TOP_K]

        elapsed_ms = (
            time.perf_counter() - start_time
        ) * 1000

        result = evaluate_ranking(
            question,
            ranked_indices,
            chunks,
            elapsed_ms,
        )

        results.append(result)

        rank_text = (
            result["expected_rank"]
            if result["expected_rank"]
            is not None
            else "Not found"
        )

        print(
            f"BM25 | "
            f"{question['id']} | "
            f"Rank: {rank_text} | "
            f"{elapsed_ms:.2f} ms"
        )

    return results


def main():
    with QUESTIONS_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        questions = json.load(file)

    print(
        f"Loaded {len(questions)} "
        "evaluation questions."
    )

    print()
    print("Loading shared FastAPI corpus...")

    chunks, embeddings = load_data()

    print(
        f"Loaded {len(chunks)} chunks."
    )

    print()
    print("Loading semantic model...")

    model = SentenceTransformer(
        MODEL_NAME
    )

    print("Building BM25 index...")

    bm25 = build_bm25(chunks)

    semantic_results = evaluate_semantic(
        questions,
        chunks,
        embeddings,
        model,
    )

    bm25_results = evaluate_bm25(
        questions,
        chunks,
        bm25,
    )

    semantic_summary = calculate_summary(
        semantic_results
    )

    bm25_summary = calculate_summary(
        bm25_results
    )

    output = {
        "settings": {
            "questions": len(questions),
            "top_k": TOP_K,
            "semantic_model": MODEL_NAME,
            "corpus_chunks": len(chunks),
        },
        "semantic": {
            "summary": semantic_summary,
            "questions": semantic_results,
        },
        "bm25": {
            "summary": bm25_summary,
            "questions": bm25_results,
        },
    }

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with RESULTS_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            output,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print()
    print("=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)

    print()
    print("Semantic:")
    print(
        json.dumps(
            semantic_summary,
            indent=2,
        )
    )

    print()
    print("BM25:")
    print(
        json.dumps(
            bm25_summary,
            indent=2,
        )
    )

    print()
    print(
        f"Results saved to: "
        f"{RESULTS_FILE}"
    )


if __name__ == "__main__":
    main()