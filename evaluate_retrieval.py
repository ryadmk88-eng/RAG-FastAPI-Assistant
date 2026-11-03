import json
import time
from pathlib import Path

from sentence_transformers import SentenceTransformer

from semantic_search import (
    load_data,
    semantic_search,
    MODEL_NAME,
)

from bm25_search import (
    build_bm25,
    bm25_search,
)


QUESTIONS_FILE = Path("evaluation_questions.json")
RESULTS_FILE = Path("results/retrieval_evaluation.json")

TOP_K = 5


def normalize_url(url):
    return url.rstrip("/")


def find_expected_rank(results, expected_url):
    expected_url = normalize_url(expected_url)

    for rank, result in enumerate(results, start=1):
        result_url = normalize_url(result["url"])

        if result_url == expected_url:
            return rank

    return None


def evaluate_method(
    method_name,
    search_function,
    questions,
):
    results = []

    for item in questions:
        question = item["question"]
        expected_url = item["expected_url"]

        start_time = time.perf_counter()

        retrieved = search_function(question)

        end_time = time.perf_counter()

        response_time_ms = (
            end_time - start_time
        ) * 1000

        expected_rank = find_expected_rank(
            retrieved,
            expected_url
        )

        result = {
            "id": item["id"],
            "question": question,
            "expected_url": expected_url,
            "expected_rank": expected_rank,
            "hit_at_1": (
                expected_rank is not None
                and expected_rank <= 1
            ),
            "hit_at_3": (
                expected_rank is not None
                and expected_rank <= 3
            ),
            "hit_at_5": (
                expected_rank is not None
                and expected_rank <= 5
            ),
            "response_time_ms": round(
                response_time_ms,
                2
            ),
            "retrieved_urls": [
                result["url"]
                for result in retrieved
            ],
        }

        results.append(result)

        rank_text = (
            str(expected_rank)
            if expected_rank
            else "Not found"
        )

        print(
            f"{method_name} | "
            f"{item['id']} | "
            f"Rank: {rank_text} | "
            f"{response_time_ms:.2f} ms"
        )

    return results


def calculate_summary(results):
    total = len(results)

    hit_1 = sum(
        result["hit_at_1"]
        for result in results
    )

    hit_3 = sum(
        result["hit_at_3"]
        for result in results
    )

    hit_5 = sum(
        result["hit_at_5"]
        for result in results
    )

    average_time = sum(
        result["response_time_ms"]
        for result in results
    ) / total

    reciprocal_ranks = []

    for result in results:
        rank = result["expected_rank"]

        if rank:
            reciprocal_ranks.append(
                1 / rank
            )
        else:
            reciprocal_ranks.append(0)

    mrr = sum(
        reciprocal_ranks
    ) / total

    return {
        "questions": total,
        "hit_at_1": round(
            hit_1 / total,
            3
        ),
        "hit_at_3": round(
            hit_3 / total,
            3
        ),
        "hit_at_5": round(
            hit_5 / total,
            3
        ),
        "mean_reciprocal_rank": round(
            mrr,
            3
        ),
        "average_response_time_ms": round(
            average_time,
            2
        ),
    }


def main():
    if not QUESTIONS_FILE.exists():
        print(
            "ERROR: evaluation_questions.json "
            "was not found."
        )
        return

    with QUESTIONS_FILE.open(
        "r",
        encoding="utf-8"
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

    semantic_model = SentenceTransformer(
        MODEL_NAME
    )

    print("Building BM25 index...")

    bm25_index = build_bm25(
        chunks
    )

    print()
    print("=" * 70)
    print("SEMANTIC RETRIEVAL")
    print("=" * 70)

    semantic_results = evaluate_method(
        "Semantic",
        lambda question: semantic_search(
            question,
            semantic_model,
            chunks,
            embeddings,
            top_k=TOP_K,
        ),
        questions,
    )

    print()
    print("=" * 70)
    print("BM25 RETRIEVAL")
    print("=" * 70)

    bm25_results = evaluate_method(
        "BM25",
        lambda question: bm25_search(
            question,
            bm25_index,
            chunks,
            top_k=TOP_K,
        ),
        questions,
    )

    semantic_summary = calculate_summary(
        semantic_results
    )

    bm25_summary = calculate_summary(
        bm25_results
    )

    final_results = {
        "configuration": {
            "questions": len(questions),
            "top_k": TOP_K,
            "embedding_model": MODEL_NAME,
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

    RESULTS_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with RESULTS_FILE.open(
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            final_results,
            file,
            ensure_ascii=False,
            indent=2,
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
            indent=2
        )
    )

    print()
    print("BM25:")
    print(
        json.dumps(
            bm25_summary,
            indent=2
        )
    )

    print()
    print(
        f"Results saved to: "
        f"{RESULTS_FILE}"
    )


if __name__ == "__main__":
    main()