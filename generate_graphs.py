import json
from pathlib import Path

import matplotlib.pyplot as plt


RESULTS_FILE = Path(
    "results/final_results_summary.json"
)

OUTPUT_DIR = Path("results/graphs")


def save_figure(filename):
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    path = OUTPUT_DIR / filename

    plt.tight_layout()
    plt.savefig(
        path,
        dpi=300,
        bbox_inches="tight",
    )
    plt.close()

    print(f"Saved: {path}")


def retrieval_accuracy_graph(data):
    semantic = data[
        "retrieval_results"
    ]["semantic"]

    bm25 = data[
        "retrieval_results"
    ]["bm25"]

    metrics = [
        "Top-1",
        "Top-3",
        "Top-5",
    ]

    semantic_values = [
        semantic["hit_at_1"] * 100,
        semantic["hit_at_3"] * 100,
        semantic["hit_at_5"] * 100,
    ]

    bm25_values = [
        bm25["hit_at_1"] * 100,
        bm25["hit_at_3"] * 100,
        bm25["hit_at_5"] * 100,
    ]

    x = range(len(metrics))
    width = 0.35

    plt.figure(figsize=(8, 5))

    plt.bar(
        [i - width / 2 for i in x],
        semantic_values,
        width,
        label="Semantic",
    )

    plt.bar(
        [i + width / 2 for i in x],
        bm25_values,
        width,
        label="BM25",
    )

    plt.xticks(
        list(x),
        metrics,
    )

    plt.ylim(0, 100)

    plt.ylabel(
        "Retrieval Accuracy (%)"
    )

    plt.xlabel(
        "Retrieval Depth"
    )

    plt.title(
        "Semantic vs BM25 Retrieval Accuracy"
    )

    plt.legend()

    save_figure(
        "retrieval_accuracy.png"
    )


def mrr_graph(data):
    semantic = data[
        "retrieval_results"
    ]["semantic"][
        "mean_reciprocal_rank"
    ]

    bm25 = data[
        "retrieval_results"
    ]["bm25"][
        "mean_reciprocal_rank"
    ]

    plt.figure(figsize=(7, 5))

    plt.bar(
        ["Semantic", "BM25"],
        [semantic, bm25],
    )

    plt.ylim(0, 1)

    plt.ylabel(
        "Mean Reciprocal Rank"
    )

    plt.title(
        "Mean Reciprocal Rank by Retrieval Method"
    )

    save_figure(
        "mean_reciprocal_rank.png"
    )


def answer_correctness_graph(data):
    semantic = data[
        "answer_quality_results"
    ]["semantic"][
        "correctness_percentage"
    ]

    bm25 = data[
        "answer_quality_results"
    ]["bm25"][
        "correctness_percentage"
    ]

    plt.figure(figsize=(7, 5))

    plt.bar(
        ["Semantic", "BM25"],
        [semantic, bm25],
    )

    plt.ylim(0, 100)

    plt.ylabel(
        "Answer Correctness (%)"
    )

    plt.title(
        "Answer Correctness by Retrieval Method"
    )

    save_figure(
        "answer_correctness.png"
    )


def retrieval_time_graph(data):
    semantic = data[
        "retrieval_results"
    ]["semantic"][
        "average_response_time_ms"
    ]

    bm25 = data[
        "retrieval_results"
    ]["bm25"][
        "average_response_time_ms"
    ]

    plt.figure(figsize=(7, 5))

    plt.bar(
        ["Semantic", "BM25"],
        [semantic, bm25],
    )

    plt.ylabel(
        "Average Retrieval Time (ms)"
    )

    plt.title(
        "Average Retrieval Response Time"
    )

    save_figure(
        "retrieval_response_time.png"
    )


def total_response_time_graph(data):
    semantic = data[
        "answer_quality_results"
    ]["semantic"][
        "average_total_response_time_ms"
    ]

    bm25 = data[
        "answer_quality_results"
    ]["bm25"][
        "average_total_response_time_ms"
    ]

    semantic_seconds = (
        semantic / 1000
    )

    bm25_seconds = (
        bm25 / 1000
    )

    plt.figure(figsize=(7, 5))

    plt.bar(
        ["Semantic", "BM25"],
        [
            semantic_seconds,
            bm25_seconds,
        ],
    )

    plt.ylabel(
        "Average Response Time (seconds)"
    )

    plt.title(
        "Average End-to-End Response Time"
    )

    save_figure(
        "total_response_time.png"
    )


def main():
    with RESULTS_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    print(
        "Generating evaluation graphs..."
    )

    retrieval_accuracy_graph(data)
    mrr_graph(data)
    answer_correctness_graph(data)
    retrieval_time_graph(data)
    total_response_time_graph(data)

    print()
    print(
        "All graphs generated successfully."
    )


if __name__ == "__main__":
    main()