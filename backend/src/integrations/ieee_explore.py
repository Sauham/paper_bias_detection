import os
import re
import requests

IEEE_API_KEY = os.getenv("IEEE_API_KEY")
IEEE_ENDPOINT = "https://ieeexploreapi.ieee.org/api/v1/search/articles"

def _clean_title(text: str) -> str:
    words = re.findall(r"[A-Za-z]{4,}", text)
    return " ".join(words[:12])

def ieee_search(section_text: str, max_results: int = 10):
    if not IEEE_API_KEY:
        return []

    title_query = _clean_title(section_text)

    params = {
        "apikey": IEEE_API_KEY,
        "format": "json",
        "max_records": max_results,
        "start_record": 1,
        "article_title": title_query,
        "content_type": "Journals"
    }

    try:
        resp = requests.get(IEEE_ENDPOINT, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return []

    results = []
    for art in data.get("articles", []):
        results.append({
            "title": art.get("title", ""),
            "abstract": art.get("abstract", ""),
            "url": art.get("pdf_url") or art.get("html_url"),
            "source": "IEEE"
        })

    return results
