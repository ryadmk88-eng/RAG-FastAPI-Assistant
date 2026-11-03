import json
import re
from pathlib import Path


INPUT_FILE = Path("data/fastapi_docs.json")
OUTPUT_FILE = Path("data/fastapi_chunks.json")

CHUNK_SIZE = 180
CHUNK_OVERLAP = 30


def split_into_sections(document):
    title = document.get("title", "Untitled")
    url = document.get("url", "")
    text = document.get("text", "")
    headings = document.get("headings", [])

    heading_set = set(headings)

    lines = text.splitlines()

    sections = []

    current_heading = title
    current_lines = []

    for line in lines:
        line = line.strip()

        if not line:
            continue

        if line in heading_set:
            if current_lines:
                sections.append(
                    {
                        "title": title,
                        "heading": current_heading,
                        "url": url,
                        "text": " ".join(current_lines),
                    }
                )

            current_heading = line
            current_lines = []

        else:
            current_lines.append(line)

    if current_lines:
        sections.append(
            {
                "title": title,
                "heading": current_heading,
                "url": url,
                "text": " ".join(current_lines),
            }
        )

    return sections


def split_sentences(text):
    """
    Split text into sentences while keeping punctuation.
    """
    sentences = re.split(r'(?<=[.!?])\s+', text)

    return [
        sentence.strip()
        for sentence in sentences
        if sentence.strip()
    ]


def chunk_text(text):
    """
    Create chunks using complete sentences where possible.
    """

    sentences = split_sentences(text)

    if not sentences:
        return []

    chunks = []

    current_sentences = []
    current_word_count = 0

    for sentence in sentences:
        sentence_words = sentence.split()
        sentence_word_count = len(sentence_words)

        if (
            current_sentences
            and current_word_count + sentence_word_count > CHUNK_SIZE
        ):
            chunk = " ".join(current_sentences)

            chunks.append(chunk)

            # Create overlap using sentences from the end
            overlap_sentences = []
            overlap_word_count = 0

            for previous_sentence in reversed(current_sentences):
                previous_words = previous_sentence.split()

                if (
                    overlap_word_count + len(previous_words)
                    > CHUNK_OVERLAP
                ):
                    break

                overlap_sentences.insert(0, previous_sentence)
                overlap_word_count += len(previous_words)

            current_sentences = overlap_sentences.copy()
            current_word_count = overlap_word_count

        current_sentences.append(sentence)
        current_word_count += sentence_word_count

    if current_sentences:
        chunks.append(" ".join(current_sentences))

    return chunks


def main():
    if not INPUT_FILE.exists():
        print("ERROR: data/fastapi_docs.json was not found.")
        return

    with INPUT_FILE.open("r", encoding="utf-8") as file:
        documents = json.load(file)

    print(f"Loaded {len(documents)} FastAPI documents.")

    all_chunks = []

    chunk_number = 1

    for document in documents:
        sections = split_into_sections(document)

        for section in sections:
            section_chunks = chunk_text(section["text"])

            for text_chunk in section_chunks:
                chunk = {
                    "chunk_id": f"chunk_{chunk_number:05d}",
                    "title": section["title"],
                    "heading": section["heading"],
                    "url": section["url"],
                    "text": text_chunk,
                }

                all_chunks.append(chunk)

                chunk_number += 1

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            all_chunks,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print()
    print("Chunking finished.")
    print(f"Created {len(all_chunks)} chunks.")
    print(f"Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()