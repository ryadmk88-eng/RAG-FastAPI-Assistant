import os

from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import SentenceTransformer

from semantic_search import (
    load_data,
    semantic_search,
    MODEL_NAME,
)


LLM_MODEL = "gpt-6-luna"
TOP_K = 5


def build_context(results):
    context_parts = []

    for number, result in enumerate(results, start=1):
        context_parts.append(
            f"""
SOURCE {number}
Title: {result['title']}
Heading: {result['heading']}
URL: {result['url']}

Documentation:
{result['text']}
"""
        )

    return "\n".join(context_parts)


def build_source_list(results):
    source_map = {}
    source_number = 1

    for result in results:
        url = result["url"]

        if url not in source_map:
            source_map[url] = {
                "number": source_number,
                "title": result["title"],
                "url": url,
            }

            source_number += 1

    return source_map


def generate_answer(question, results, client):
    context = build_context(results)

    prompt = f"""
You are a technical documentation assistant for FastAPI.

Answer the user's question using ONLY the FastAPI documentation
provided below.

Rules:
- Do not invent information.
- If the documentation does not contain enough information, say so.
- Give a clear and concise technical answer.
- Cite the supporting evidence using the source numbers provided below.
- Do not use outside knowledge.

USER QUESTION:
{question}

FASTAPI DOCUMENTATION:
{context}
"""

    response = client.responses.create(
        model=LLM_MODEL,
        input=prompt,
    )

    return response.output_text


def main():
    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        print("ERROR: OPENAI_API_KEY was not found.")
        return

    client = OpenAI(api_key=api_key)

    print("Loading FastAPI retrieval system...")

    chunks, embeddings = load_data()

    embedding_model = SentenceTransformer(MODEL_NAME)

    print("RAG assistant is ready.")
    print("Type 'exit' to stop.")
    print()

    while True:
        question = input("Ask a FastAPI question: ").strip()

        if question.lower() == "exit":
            break

        if not question:
            continue

        results = semantic_search(
            question,
            embedding_model,
            chunks,
            embeddings,
            top_k=TOP_K,
        )

        print()
        print("Generating answer...")
        print()

        try:
            answer = generate_answer(
                question,
                results,
                client,
            )

            print("=" * 80)
            print()
            print(answer)
            print()
            print("Sources:")

            source_map = build_source_list(results)

            for source in source_map.values():
                print(
                    f"[Source {source['number']}] "
                    f"{source['title']} - {source['url']}"
                )

            print()
            print("=" * 80)
            print()

        except Exception as error:
            print(f"ERROR: {error}")
            print()


if __name__ == "__main__":
    main()