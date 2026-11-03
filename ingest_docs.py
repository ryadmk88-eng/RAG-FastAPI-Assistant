import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE_URL = "https://fastapi.tiangolo.com/"

response = requests.get(BASE_URL, timeout=30)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

links = set()

for a_tag in soup.find_all("a", href=True):
    full_url = urljoin(BASE_URL, a_tag["href"])
    full_url = full_url.split("#")[0]

    if full_url.startswith(BASE_URL):
        links.add(full_url)

with open("data/fastapi_urls.txt", "w", encoding="utf-8") as file:
    for link in sorted(links):
        file.write(link + "\n")

print(f"Saved {len(links)} FastAPI links")