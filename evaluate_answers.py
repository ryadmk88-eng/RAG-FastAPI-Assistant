import json
import os
import re
import time
from pathlib import Path

import numpy as np
from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import SentenceTransformer

from semantic_search import load_data, MODEL_NAME
from bm25_search import build_bm25


QUESTIONS_FILE = Path("evaluation_questions.json")
RESULTS_DIR = Path("results")
RESULTS_FILE = RESULTS_DIR / "answer_evaluation.json"

TOP_K = 5
LLM_MODEL = "gpt-6-luna"


def tokenize(text):
    return re.findall(r"\b\w+\b", text.lower())


def save_results(data):
    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with RESULTS_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False,
        )


def load_existing_results():
    if not RESULTS_FILE.exists():
        return {
            "settings": {
                "top_k": TOP_K,
                "embedding_model": MODEL_NAME,
                "llm_model": LLM_MODEL,
            },
            "answers": [],
        }

    with RESULTS_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def build_context(retrieved_chunks):
    source_numbers = {}
    next_source_number = 1

    context_parts = []
    sources = []

    for chunk in retrieved_chunks:
        url = chunk["url"]

        if url not in source_numbers:
            source_numbers[url] = next_source_number

            sources.append(
                {
                    "source_number": next_source_number,
                    "title": chunk["title"],
                    "url": url,
                }
            )

            next_source_number += 1

        source_number = source_numbers[url]

        heading = chunk.get(
            "heading",
            ""
        ).strip()

        text = chunk.get(
            "text",
            ""
        ).strip()

        context_parts.append(
            (
                f"[Source {source_number}]\n"
                f"Title: {chunk['title']}\n"
                f"Heading: {heading}\n"
                f"URL: {url}\n"
                f"Content:\n{text}"
            )
        )

    context = "\n\n---\n\n".join(
        context_parts
    )

    return context, sources


def generate_answer(
    client,
    question,
    retrieved_chunks,
):
    context, sources = build_context(
        retrieved_chunks
    )

    prompt = f"""
You are a technical documentation assistant for FastAPI.

Answer the user's question using ONLY the FastAPI documentation
provided in the context below.

Rules:
1. Do not use outside knowledge.
2. Do not invent information.
3. If the supplied documentation is insufficient, clearly say so.
4. Keep the answer clear and concise.
5. Support factual statements with citations such as [Source 1].
6. Only cite source numbers that appear in the supplied context.
7. Do not create fake URLs or fake citations.

Question:
{question}

FastAPI documentation context:
{context}
""".strip()

    start_time = time.perf_counter()

    response = client.responses.create(
        model=LLM_MODEL,
        input=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    generation_time_ms = (
        time.perf_counter() - start_time
    ) * 1000

    return (
        response.output_text.strip(),
        sources,
        generation_time_ms,
    )


def semantic_retrieve(
    question,
    chunks,
    embeddings,
    model,
):
    start_time = time.perf_counter()

    query_embedding = model.encode(
        question,
        normalize_embeddings=True,
    )

    scores = embeddings @ query_embedding

    ranked_indices = np.argsort(
        scores
    )[::-1][:TOP_K]

    retrieval_time_ms = (
        time.perf_counter() - start_time
    ) * 1000

    retrieved_chunks = [
        chunks[index]
        for index in ranked_indices
    ]

    return (
        retrieved_chunks,
        retrieval_time_ms,
    )


def bm25_retrieve(
    question,
    chunks,
    bm25,
):
    start_time = time.perf_counter()

    query_tokens = tokenize(question)

    scores = bm25.get_scores(
        query_tokens
    )

    ranked_indices = np.argsort(
        scores
    )[::-1][:TOP_K]

    retrieval_time_ms = (
        time.perf_counter() - start_time
    ) * 1000

    retrieved_chunks = [
        chunks[index]
        for index in ranked_indices
    ]

    return (
        retrieved_chunks,
        retrieval_time_ms,
    )


def already_completed(
    results,
    question_id,
    method,
):
    for item in results["answers"]:
        if (
            item["id"] == question_id
            and item["retrieval_method"] == method
        ):
            return True

    return False


def evaluate_method(
    method,
    questions,
    chunks,
    embeddings,
    semantic_model,
    bm25,
    client,
    results,
):
    print()
    print("=" * 70)
    print(
        f"{method.upper()} ANSWER GENERATION"
    )
    print("=" * 70)

    for question in questions:
        question_id = question["id"]
        question_text = question["question"]

        if already_completed(
            results,
            question_id,
            method,
        ):
            print(
                f"{method} | "
                f"{question_id} | "
                "Already completed - skipped"
            )
            continue

        if method == "semantic":
            (
                retrieved_chunks,
                retrieval_time_ms,
            ) = semantic_retrieve(
                question_text,
                chunks,
                embeddings,
                semantic_model,
            )

        elif method == "bm25":
            (
                retrieved_chunks,
                retrieval_time_ms,
            ) = bm25_retrieve(
                question_text,
                chunks,
                bm25,
            )

        else:
            raise ValueError(
                f"Unknown retrieval method: "
                f"{method}"
            )

        try:
            (
                answer,
                sources,
                generation_time_ms,
            ) = generate_answer(
                client,
                question_text,
                retrieved_chunks,
            )

        except Exception as error:
            print(
                f"{method} | "
                f"{question_id} | "
                f"ERROR: {error}"
            )

            save_results(results)

            continue

        total_time_ms = (
            retrieval_time_ms
            + generation_time_ms
        )

        result = {
            "id": question_id,
            "question": question_text,
            "retrieval_method": method,
            "key_points": question.get(
                "key_points",
                [],
            ),
            "answer": answer,
            "sources": sources,
            "retrieved_urls": [
                chunk["url"]
                for chunk in retrieved_chunks
            ],
            "retrieval_time_ms": round(
                retrieval_time_ms,
                2,
            ),
            "generation_time_ms": round(
                generation_time_ms,
                2,
            ),
            "total_time_ms": round(
                total_time_ms,
                2,
            ),
            "manual_evaluation": {
                "correctness_score": None,
                "source_support_score": None,
                "unsupported_claims": None,
                "notes": "",
            },
        }

        results["answers"].append(result)

        save_results(results)

        print(
            f"{method} | "
            f"{question_id} | "
            f"Generated | "
            f"{total_time_ms:.2f} ms"
        )


def print_summary(results):
    semantic_answers = [
        item
        for item in results["answers"]
        if item["retrieval_method"]
        == "semantic"
    ]

    bm25_answers = [
        item
        for item in results["answers"]
        if item["retrieval_method"]
        == "bm25"
    ]

    print()
    print("=" * 70)
    print("ANSWER EVALUATION DATASET SUMMARY")
    print("=" * 70)

    print(
        f"Semantic answers: "
        f"{len(semantic_answers)}"
    )

    print(
        f"BM25 answers: "
        f"{len(bm25_answers)}"
    )

    print(
        f"Total answers: "
        f"{len(results['answers'])}"
    )

    if semantic_answers:
        semantic_average = sum(
            item["total_time_ms"]
            for item in semantic_answers
        ) / len(semantic_answers)

        print(
            "Semantic average total "
            f"time: {semantic_average:.2f} ms"
        )

    if bm25_answers:
        bm25_average = sum(
            item["total_time_ms"]
            for item in bm25_answers
        ) / len(bm25_answers)

        print(
            "BM25 average total "
            f"time: {bm25_average:.2f} ms"
        )

    print()
    print(
        f"Results saved to: "
        f"{RESULTS_FILE}"
    )


def main():
    load_dotenv()

    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY was not found. "
            "Check your .env file."
        )

    client = OpenAI()

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
    print(
        "Loading FastAPI chunks "
        "and embeddings..."
    )

    chunks, embeddings = load_data()

    print(
        f"Loaded {len(chunks)} chunks."
    )

    print()
    print(
        "Loading semantic model..."
    )

    semantic_model = (
        SentenceTransformer(
            MODEL_NAME
        )
    )

    print(
        "Building BM25 index..."
    )

    bm25 = build_bm25(chunks)

    results = load_existing_results()

    evaluate_method(
        "semantic",
        questions,
        chunks,
        embeddings,
        semantic_model,
        bm25,
        client,
        results,
    )

    evaluate_method(
        "bm25",
        questions,
        chunks,
        embeddings,
        semantic_model,
        bm25,
        client,
        results,
    )

    print_summary(results)


if __name__ == "__main__":
    main()