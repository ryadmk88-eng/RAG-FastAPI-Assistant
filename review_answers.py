import json
import random
import re
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

from semantic_search import load_data, MODEL_NAME
from bm25_search import build_bm25


ANSWERS_FILE = Path("results/answer_evaluation.json")
REVIEW_ORDER_FILE = Path("results/answer_review_order.json")

TOP_K = 5
REVIEW_SEED = 2026


def tokenize(text):
    return re.findall(r"\b\w+\b", text.lower())


def load_answers():
    with ANSWERS_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def save_answers(data):
    with ANSWERS_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False,
        )


def answer_key(item):
    return (
        f"{item['id']}::"
        f"{item['retrieval_method']}"
    )


def get_review_order(answers):
    available_keys = [
        answer_key(item)
        for item in answers
    ]

    if REVIEW_ORDER_FILE.exists():
        with REVIEW_ORDER_FILE.open(
            "r",
            encoding="utf-8",
        ) as file:
            saved_order = json.load(file)

        valid_order = [
            key
            for key in saved_order
            if key in available_keys
        ]

        missing = [
            key
            for key in available_keys
            if key not in valid_order
        ]

        valid_order.extend(missing)

        return valid_order

    order = available_keys.copy()

    random_generator = random.Random(
        REVIEW_SEED
    )

    random_generator.shuffle(order)

    REVIEW_ORDER_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with REVIEW_ORDER_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            order,
            file,
            indent=2,
        )

    return order


def is_completed(item):
    manual = item.get(
        "manual_evaluation",
        {},
    )

    return (
        manual.get("correctness_score")
        is not None
        and manual.get("source_support_score")
        is not None
        and manual.get("unsupported_claims")
        is not None
    )


def semantic_retrieve(
    question,
    chunks,
    embeddings,
    model,
):
    query_embedding = model.encode(
        question,
        normalize_embeddings=True,
    )

    scores = embeddings @ query_embedding

    ranked_indices = np.argsort(
        scores
    )[::-1][:TOP_K]

    return [
        chunks[index]
        for index in ranked_indices
    ]


def bm25_retrieve(
    question,
    chunks,
    bm25,
):
    scores = bm25.get_scores(
        tokenize(question)
    )

    ranked_indices = np.argsort(
        scores
    )[::-1][:TOP_K]

    return [
        chunks[index]
        for index in ranked_indices
    ]


def get_retrieved_chunks(
    item,
    chunks,
    embeddings,
    semantic_model,
    bm25,
):
    method = item[
        "retrieval_method"
    ]

    question = item["question"]

    if method == "semantic":
        return semantic_retrieve(
            question,
            chunks,
            embeddings,
            semantic_model,
        )

    if method == "bm25":
        return bm25_retrieve(
            question,
            chunks,
            bm25,
        )

    raise ValueError(
        f"Unknown retrieval method: "
        f"{method}"
    )


def group_sources(retrieved_chunks):
    source_numbers = {}
    grouped_sources = []

    for chunk in retrieved_chunks:
        url = chunk["url"]

        if url not in source_numbers:
            source_number = (
                len(source_numbers) + 1
            )

            source_numbers[
                url
            ] = source_number

            grouped_sources.append(
                {
                    "source_number":
                        source_number,
                    "title":
                        chunk["title"],
                    "url":
                        url,
                    "chunks": [],
                }
            )

        source_number = (
            source_numbers[url]
        )

        source = next(
            source
            for source
            in grouped_sources
            if source[
                "source_number"
            ] == source_number
        )

        source["chunks"].append(
            {
                "heading":
                    chunk.get(
                        "heading",
                        "",
                    ),
                "text":
                    chunk.get(
                        "text",
                        "",
                    ),
            }
        )

    return grouped_sources


def print_separator():
    print()
    print("=" * 80)
    print()


def display_item(
    item,
    position,
    total,
    retrieved_chunks,
):
    print_separator()

    print(
        f"BLIND REVIEW "
        f"{position}/{total}"
    )

    print(
        "Retrieval method: HIDDEN"
    )

    print()
    print("QUESTION")
    print("-" * 80)
    print(item["question"])

    print()
    print("EXPECTED KEY POINTS")
    print("-" * 80)

    for number, point in enumerate(
        item.get(
            "key_points",
            [],
        ),
        start=1,
    ):
        print(
            f"{number}. {point}"
        )

    print()
    print("GENERATED ANSWER")
    print("-" * 80)
    print(item["answer"])

    print()
    print("RETRIEVED DOCUMENTATION")
    print("-" * 80)

    grouped_sources = group_sources(
        retrieved_chunks
    )

    for source in grouped_sources:
        print()
        print(
            f"[Source "
            f"{source['source_number']}]"
        )

        print(
            f"Title: "
            f"{source['title']}"
        )

        print(
            f"URL: "
            f"{source['url']}"
        )

        for chunk_number, chunk in enumerate(
            source["chunks"],
            start=1,
        ):
            print()

            heading = (
                chunk["heading"]
                or "(No heading)"
            )

            print(
                f"Chunk {chunk_number}"
            )

            print(
                f"Heading: {heading}"
            )

            print(
                chunk["text"]
            )


def get_score(
    prompt,
    minimum,
    maximum,
):
    while True:
        value = input(
            prompt
        ).strip().lower()

        if value == "q":
            return None

        try:
            score = int(value)

            if (
                minimum
                <= score
                <= maximum
            ):
                return score

        except ValueError:
            pass

        print(
            f"Enter a number from "
            f"{minimum} to {maximum}, "
            "or q to quit."
        )


def get_unsupported_claims():
    while True:
        value = input(
            "Unsupported factual claims "
            "(0 or more, q to quit): "
        ).strip().lower()

        if value == "q":
            return None

        try:
            count = int(value)

            if count >= 0:
                return count

        except ValueError:
            pass

        print(
            "Enter 0 or a positive "
            "whole number, or q to quit."
        )


def print_rubric():
    print()
    print("=" * 80)
    print("BLIND ANSWER QUALITY REVIEW")
    print("=" * 80)

    print(
        """
You will NOT be shown whether an answer came from Semantic or BM25.

CORRECTNESS SCORE
3 = Fully correct and addresses the question/key points.
2 = Mostly correct, with a minor omission or minor issue.
1 = Partly correct, with important information missing or incorrect.
0 = Incorrect, misleading, or does not answer the question.

SOURCE SUPPORT SCORE
3 = All important factual claims are supported by the retrieved documentation.
2 = Mostly supported, with a minor unsupported claim or gap.
1 = Only partly supported; important claims lack support.
0 = Unsupported, contradicted by the supplied documentation, or fabricated.

UNSUPPORTED CLAIMS
Count clear factual claims in the answer that are not supported by the
retrieved FastAPI documentation shown to you.

Type q at a scoring prompt if you want to stop.
Your completed reviews are saved automatically.
""".strip()
    )


def calculate_summary(data):
    print()
    print("=" * 80)
    print("CURRENT REVIEW SUMMARY")
    print("=" * 80)

    for method in [
        "semantic",
        "bm25",
    ]:
        reviewed = [
            item
            for item in data[
                "answers"
            ]
            if (
                item[
                    "retrieval_method"
                ] == method
                and is_completed(item)
            )
        ]

        print()
        print(
            f"{method.upper()}: "
            f"{len(reviewed)} reviewed"
        )

        if not reviewed:
            continue

        correctness = [
            item[
                "manual_evaluation"
            ][
                "correctness_score"
            ]
            for item in reviewed
        ]

        support = [
            item[
                "manual_evaluation"
            ][
                "source_support_score"
            ]
            for item in reviewed
        ]

        unsupported = [
            item[
                "manual_evaluation"
            ][
                "unsupported_claims"
            ]
            for item in reviewed
        ]

        print(
            "Average correctness: "
            f"{sum(correctness) / len(correctness):.2f}"
            " / 3"
        )

        print(
            "Average source support: "
            f"{sum(support) / len(support):.2f}"
            " / 3"
        )

        print(
            "Total unsupported claims: "
            f"{sum(unsupported)}"
        )


def main():
    data = load_answers()

    answers = data.get(
        "answers",
        [],
    )

    if not answers:
        print(
            "No generated answers found in "
            "results/answer_evaluation.json."
        )

        return

    print(
        "Loading FastAPI retrieval data..."
    )

    chunks, embeddings = load_data()

    print(
        f"Loaded {len(chunks)} chunks."
    )

    print(
        "Loading semantic model..."
    )

    semantic_model = SentenceTransformer(
        MODEL_NAME
    )

    print(
        "Building BM25 index..."
    )

    bm25 = build_bm25(
        chunks
    )

    order = get_review_order(
        answers
    )

    lookup = {
        answer_key(item): item
        for item in answers
    }

    remaining_keys = [
        key
        for key in order
        if (
            key in lookup
            and not is_completed(
                lookup[key]
            )
        )
    ]

    print_rubric()

    if not remaining_keys:
        print()
        print(
            "All answers have already "
            "been reviewed."
        )

        calculate_summary(data)

        return

    print()
    print(
        f"Remaining answers to review: "
        f"{len(remaining_keys)}"
    )

    total = len(order)

    for key in order:
        if key not in lookup:
            continue

        item = lookup[key]

        if is_completed(item):
            continue

        position = (
            order.index(key) + 1
        )

        retrieved_chunks = (
            get_retrieved_chunks(
                item,
                chunks,
                embeddings,
                semantic_model,
                bm25,
            )
        )

        display_item(
            item,
            position,
            total,
            retrieved_chunks,
        )

        print()
        print("YOUR SCORES")
        print("-" * 80)

        correctness = get_score(
            "Correctness (0-3, q to quit): ",
            0,
            3,
        )

        if correctness is None:
            save_answers(data)
            print(
                "\nReview stopped. "
                "Progress saved."
            )
            calculate_summary(data)
            return

        support = get_score(
            "Source support (0-3, q to quit): ",
            0,
            3,
        )

        if support is None:
            save_answers(data)
            print(
                "\nReview stopped. "
                "Progress saved."
            )
            calculate_summary(data)
            return

        unsupported = (
            get_unsupported_claims()
        )

        if unsupported is None:
            save_answers(data)
            print(
                "\nReview stopped. "
                "Progress saved."
            )
            calculate_summary(data)
            return

        notes = input(
            "Notes (optional): "
        ).strip()

        item[
            "manual_evaluation"
        ] = {
            "correctness_score":
                correctness,
            "source_support_score":
                support,
            "unsupported_claims":
                unsupported,
            "notes":
                notes,
        }

        save_answers(data)

        print(
            "\nSaved."
        )

    print()
    print(
        "All 40 answers have "
        "been reviewed."
    )

    calculate_summary(data)


if __name__ == "__main__":
    main()