import json
import time
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


URL_FILE = Path("data/fastapi_urls.txt")
OUTPUT_FILE = Path("data/fastapi_docs.json")

HEADERS = {
    "User-Agent": "RAG-FastAPI-Assistant/1.0"
}

# FastAPI translated documentation prefixes that we do not want
LANGUAGE_PREFIXES = {
    "de", "es", "fr", "hi", "ja", "ko",
    "pt", "ru", "tr", "uk", "zh", "zh-hant"
}


def is_english_url(url):
    path_parts = urlparse(url).path.strip("/").split("/")

    if not path_parts or path_parts == [""]:
        return True

    return path_parts[0].lower() not in LANGUAGE_PREFIXES


def clean_page(html, url):
    soup = BeautifulSoup(html, "html.parser")

    # Remove content not useful for our RAG corpus
    for tag in soup(
        ["script", "style", "nav", "footer", "header", "noscript", "svg"]
    ):
        tag.decompose()

    content = (
        soup.find("article")
        or soup.find("main")
        or soup.find("div", class_="md-content")
        or soup.body
    )

    if content is None:
        return None

    # Page title
    h1 = content.find("h1")

    if h1:
        title = h1.get_text(" ", strip=True).replace("¶", "").strip()
    elif soup.title:
        title = soup.title.get_text(" ", strip=True).replace("¶", "").strip()
    else:
        title = url

    # Collect headings from the page
    headings = []

    for heading in content.find_all(["h1", "h2", "h3"]):
        heading_text = heading.get_text(" ", strip=True)
        heading_text = heading_text.replace("¶", "").strip()

        if heading_text and heading_text not in headings:
            headings.append(heading_text)

    # Extract page text
    text = content.get_text("\n", strip=True)

    clean_lines = []

    for line in text.splitlines():
        line = " ".join(line.split())
        line = line.replace("¶", "").strip()

        if line:
            clean_lines.append(line)

    clean_text = "\n".join(clean_lines)

    if not clean_text:
        return None

    return {
        "title": title,
        "url": url,
        "headings": headings,
        "text": clean_text
    }


def main():
    if not URL_FILE.exists():
        print("ERROR: data/fastapi_urls.txt was not found.")
        return

    all_urls = URL_FILE.read_text(encoding="utf-8").splitlines()

    # Keep English FastAPI documentation only
    urls = [url for url in all_urls if is_english_url(url)]

    documents = []

    print(f"Found {len(all_urls)} total URLs.")
    print(f"Keeping {len(urls)} English URLs.")

    for number, url in enumerate(urls, start=1):
        try:
            print(f"[{number}/{len(urls)}] Scraping: {url}")

            response = requests.get(
                url,
                headers=HEADERS,
                timeout=30
            )

            response.raise_for_status()

            document = clean_page(response.text, url)

            if document:
                documents.append(document)

        except requests.RequestException as error:
            print(f"Failed: {url}")
            print(f"Reason: {error}")

        time.sleep(0.2)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            documents,
            file,
            ensure_ascii=False,
            indent=2
        )

    print()
    print("Finished.")
    print(f"Saved {len(documents)} English documents.")
    print(f"Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()