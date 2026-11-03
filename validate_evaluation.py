import json
from pathlib import Path


QUESTIONS_FILE = Path("evaluation_questions.json")
CHUNKS_FILE = Path("data/fastapi_chunks.json")


def normalize_url(url):
    return url.rstrip("/")


def get_expected_urls(question):
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


def main():
    with QUESTIONS_FILE.open(
        "r",
        encoding="utf-8"
    ) as file:
        questions = json.load(file)

    with CHUNKS_FILE.open(
        "r",
        encoding="utf-8"
    ) as file:
        chunks = json.load(file)

    corpus_urls = {
        normalize_url(chunk["url"])
        for chunk in chunks
    }

    print(f"Questions: {len(questions)}")
    print(f"Unique corpus URLs: {len(corpus_urls)}")

    print()
    print("=" * 70)
    print("EXPECTED URL CHECK")
    print("=" * 70)

    missing = []

    for item in questions:
        expected_urls = get_expected_urls(item)

        missing_urls = [
            url
            for url in expected_urls
            if url not in corpus_urls
        ]

        if not missing_urls:
            print(f"{item['id']}: OK")
        else:
            print(f"{item['id']}: MISSING")

            missing.append(
                {
                    "id": item["id"],
                    "missing_urls": missing_urls,
                }
            )

    print()

    if missing:
        print(
            "Some expected sources are missing "
            "from the corpus:"
        )

        for item in missing:
            for url in item["missing_urls"]:
                print(
                    f"- {item['id']}: {url}"
                )
    else:
        print(
            "All expected sources exist "
            "in the FastAPI corpus."
        )


if __name__ == "__main__":
    main()