import re
import time
import os
import json
import requests
from typing import Dict, List, Tuple

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.integrations.ieee_explore import ieee_search
from openai import OpenAI


# -------------------- CONFIG -------------------- #

SEMANTIC_SCHOLAR_SEARCH = "https://api.semanticscholar.org/graph/v1/paper/search"
OPENALEX_SEARCH = "https://api.openalex.org/works"

IEEE_THRESHOLD = 12.0
SS_THRESHOLD = 10.0
OPENALEX_THRESHOLD = 6.0


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


# -------------------- UTILS -------------------- #

def _normalize_whitespace(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"[\u00A0\t]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def similarity_percent(a: str, b: str) -> float:
    vectorizer = TfidfVectorizer(stop_words="english")
    try:
        X = vectorizer.fit_transform([a or "", b or ""])
        sim = cosine_similarity(X[0:1], X[1:2]).ravel()[0]
    except ValueError:
        sim = 0.0
    return max(0.0, min(1.0, float(sim))) * 100.0


def categorize_similarity(pct: float) -> str:
    if pct <= 15:
        return "Low similarity"
    if pct <= 30:
        return "Moderate similarity"
    return "High textual similarity(review recommended)"


# -------------------- METADATA -------------------- #

def extract_metadata(full_text: str) -> Dict[str, str]:
    lines = [l.strip() for l in full_text.splitlines() if l.strip()]
    title = lines[0][:200] if lines else ""

    year_match = re.search(r"(19|20)\d{2}", full_text)
    year = year_match.group(0) if year_match else ""

    doi_match = re.search(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", full_text, re.I)
    doi = doi_match.group(0) if doi_match else ""

    return {"title": title, "year": year, "doi": doi}


# -------------------- SECTIONS -------------------- #

import re

def extract_sections(text: str) -> dict:
    """
    Extracts major academic sections safely.
    Always returns Title, Abstract, Methodology, Conclusions.
    Never references metadata.
    """

    if not text:
        return {
            "Title": "",
            "Abstract": "",
            "Methodology": "",
            "Conclusions": ""
        }

    text = text.replace("\r", "\n")
    lower = text.lower()

    # ---------- TITLE ----------
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    title = lines[0][:200] if lines else ""

    # ---------- SECTION PATTERNS ----------
    patterns = {
        "Abstract": r"\babstract\b",
        "Methodology": r"\b(methodology|methods|materials and methods|approach)\b",
        "Conclusions": r"\b(conclusion|conclusions|discussion)\b",
    }

    indices = {}
    for name, pat in patterns.items():
        m = re.search(pat, lower)
        if m:
            indices[name] = m.start()

    ordered = sorted(indices.items(), key=lambda x: x[1])

    sections = {}

    for i, (name, start) in enumerate(ordered):
        end = ordered[i + 1][1] if i + 1 < len(ordered) else len(text)
        sections[name] = text[start:end].strip()

    # ---------- FALLBACKS ----------
    sections.setdefault("Abstract", text[:1500])
    sections.setdefault("Methodology", text[1500:5000])
    sections.setdefault("Conclusions", text[-2000:])

    return {
        "Title": title,
        "Abstract": sections["Abstract"],
        "Methodology": sections["Methodology"],
        "Conclusions": sections["Conclusions"]
    }

# -------------------- SEARCH PROVIDERS -------------------- #

def _semantic_scholar_search(query: str, max_results: int) -> List[Dict]:
    try:
        resp = requests.get(
            SEMANTIC_SCHOLAR_SEARCH,
            params={"query": query, "limit": max_results, "fields": "title,url,abstract"},
            timeout=12
        )
        if resp.status_code == 429:
            return []
        resp.raise_for_status()
        data = resp.json() or {}
        return [{
            "title": p.get("title", ""),
            "abstract": p.get("abstract", ""),
            "url": p.get("url", ""),
            "source": "SemanticScholar"
        } for p in data.get("data", [])]
    except Exception:
        return []


def _openalex_search(query: str, max_results: int) -> List[Dict]:
    try:
        resp = requests.get(
            OPENALEX_SEARCH,
            params={
                "search": query,
                "filter": "type:journal-article,has_abstract:true",
                "per_page": max_results
            },
            timeout=12
        )
        resp.raise_for_status()
        data = resp.json() or {}
        return [{
            "title": r.get("title", ""),
            "abstract": " ".join(r.get("abstract_inverted_index", {}).keys()),
            "url": r.get("id", ""),
            "source": "OpenAlex"
        } for r in data.get("results", [])]
    except Exception:
        return []


def _openai_web_fallback(text: str) -> List[Dict]:
    if not openai_client:
        return []

    prompt = f"""
You are a plagiarism detection assistant.
Check whether the following academic text likely appears on the public web.
If yes, identify a probable source (title or website).

Respond ONLY in JSON:
{{
  "found": true/false,
  "source_title": "",
  "source_url": ""
}}

Text:
\"\"\"{text[:1000]}\"\"\"
"""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=120
        )
        content = response.choices[0].message.content.strip()
        data = json.loads(content)

        if data.get("found"):
            return [{
                "title": data.get("source_title", ""),
                "abstract": "",
                "url": data.get("source_url", ""),
                "source": "OpenAI-Web"
            }]
    except Exception:
        return []

    return []


# -------------------- CORE ANALYSIS -------------------- #
def build_search_query(text: str) -> str:
    """
    Build a short, effective academic search query
    from section text.
    """
    words = re.findall(r"[A-Za-z]{4,}", text)
    return " ".join(words[:12])


def search_related_papers(section_text: str, max_results: int = 10):
    query = build_search_query(section_text)
    if not query:
        return []

    results = []

    try:
        resp = requests.get(
            "https://api.semanticscholar.org/graph/v1/paper/search",
            params={
                "query": query,
                "limit": max_results,
                "fields": "title,abstract,url"
            },
            timeout=10
        )
        if resp.status_code == 200:
            data = resp.json()
            for item in data.get("data", []):
                results.append({
                    "title": item.get("title", ""),
                    "abstract": item.get("abstract", ""),
                    "url": item.get("url", "")
                })
    except Exception as e:
        print("Semantic Scholar error:", e)

    return results

def analyze_section(section_text: str, top_k: int = 5):

    # ---- EARLY EXIT ----
    if not section_text or len(section_text.strip()) < 30:
        return {
            "best_similarity_percent": 0.0,
            "category": "Low similarity",
            "matches": []
        }

    # ---- NORMAL LOGIC ----
    candidates = search_related_papers(section_text)
    scored = []

    for paper in candidates:
        content = f"{paper.get('title','')} {paper.get('abstract','')}"
        pct = similarity_percent(section_text, content)
        scored.append((pct, paper))

    scored.sort(key=lambda x: x[0], reverse=True)

    best_pct = scored[0][0] if scored else 0.0

    return {
        "best_similarity_percent": round(best_pct, 2),
        "category": categorize_similarity(best_pct),
        "matches": [
            {
                "percent": round(p, 2),
                "title": d.get("title", ""),
                "url": d.get("url", "")
            }
            for p, d in scored[:top_k]
        ]
    }



def analyze_plagiarism(full_text: str) -> Dict[str, object]:
    sections = extract_sections(full_text)

    report = {
        "sections": {},
        "overall_percent": 0.0
    }

    # Weights: Title, Abstract, Methodology, Conclusions
    weights = np.array([0.05, 0.45, 0.45, 0.05])
    values = []

    for name in ["Title", "Abstract", "Methodology", "Conclusions"]:
        section_text = sections.get(name, "")

        # Run similarity analysis (NO metadata)
        result = analyze_section(section_text)

        # ✅ INCLUDE SECTION TEXT (critical fix)
        report["sections"][name] = {
            "text": section_text,
            "best_similarity_percent": result.get("best_similarity_percent", 0.0),
            "category": result.get("category", ""),
            "matches": result.get("matches", [])
        }

        values.append(result.get("best_similarity_percent", 0.0))

    # Overall weighted similarity
    report["overall_percent"] = float(
        np.round(np.dot(weights, np.array(values)), 2)
    )
    report["overall_category"] = categorize_similarity(report["overall_percent"])

    return report
