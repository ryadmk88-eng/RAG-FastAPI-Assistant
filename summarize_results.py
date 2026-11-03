import json
from pathlib import Path


RETRIEVAL_FILE = Path(
    "results/retrieval_evaluation.json"
)

ANSWER_FILE = Path(
    "results/answer_evaluation.json"
)

OUTPUT_FILE = Path(
    "results/final_results_summary.json"
)


def average(values):
    if not values:
        return 0

    return sum(values) / len(values)


def calculate_answer_summary(
    answers,
    method,
):
    selected = [
        item
        for item in answers
        if item["retrieval_method"] == method
    ]

    reviewed = [
        item
        for item in selected
        if item.get(
            "manual_evaluation",
            {}
        ).get(
            "correctness_score"
        ) is not None
    ]

    correctness = [
        item["manual_evaluation"][
            "correctness_score"
        ]
        for item in reviewed
    ]

    source_support = [
        item["manual_evaluation"][
            "source_support_score"
        ]
        for item in reviewed
    ]

    unsupported_claims = [
        item["manual_evaluation"][
            "unsupported_claims"
        ]
        for item in reviewed
    ]

    total_times = [
        item["total_time_ms"]
        for item in selected
    ]

    avg_correctness = average(
        correctness
    )

    return {
        "answers_reviewed": len(reviewed),
        "average_correctness_score":
            round(avg_correctness, 3),
        "correctness_percentage":
            round(
                (
                    avg_correctness / 3
                ) * 100,
                1,
            ),
        "average_source_support_score":
            round(
                average(source_support),
                3,
            ),
        "total_unsupported_claims":
            sum(unsupported_claims),
        "average_total_response_time_ms":
            round(
                average(total_times),
                2,
            ),
    }


def main():
    with RETRIEVAL_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        retrieval_data = json.load(file)

    with ANSWER_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        answer_data = json.load(file)

    semantic_retrieval = (
        retrieval_data["semantic"]["summary"]
    )

    bm25_retrieval = (
        retrieval_data["bm25"]["summary"]
    )

    answers = answer_data["answers"]

    semantic_answers = (
        calculate_answer_summary(
            answers,
            "semantic",
        )
    )

    bm25_answers = (
        calculate_answer_summary(
            answers,
            "bm25",
        )
    )

    output = {
        "evaluation_stage":
            "20-question candidate evaluation",
        "retrieval_results": {
            "semantic": semantic_retrieval,
            "bm25": bm25_retrieval,
        },
        "answer_quality_results": {
            "semantic": semantic_answers,
            "bm25": bm25_answers,
        },
    }

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_FILE.open(
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
    print("COMBINED EVALUATION RESULTS")
    print("=" * 70)

    print()
    print("SEMANTIC RETRIEVAL")
    print(
        json.dumps(
            semantic_retrieval,
            indent=2,
        )
    )

    print()
    print("SEMANTIC ANSWER QUALITY")
    print(
        json.dumps(
            semantic_answers,
            indent=2,
        )
    )

    print()
    print("BM25 RETRIEVAL")
    print(
        json.dumps(
            bm25_retrieval,
            indent=2,
        )
    )

    print()
    print("BM25 ANSWER QUALITY")
    print(
        json.dumps(
            bm25_answers,
            indent=2,
        )
    )

    print()
    print(
        f"Summary saved to: "
        f"{OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()