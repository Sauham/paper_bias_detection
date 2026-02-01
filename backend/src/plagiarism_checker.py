import re
import time
import os
import json
import logging
import requests
from typing import Dict, List, Tuple

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.integrations.ieee_explore import ieee_search

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------- CONFIG -------------------- #

SEMANTIC_SCHOLAR_SEARCH = "https://api.semanticscholar.org/graph/v1/paper/search"
OPENALEX_SEARCH = "https://api.openalex.org/works"

# Similarity thresholds
IEEE_THRESHOLD = 12.0
SS_THRESHOLD = 10.0
OPENALEX_THRESHOLD = 6.0


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
    """Search OpenAlex for academic papers."""
    try:
        resp = requests.get(
            OPENALEX_SEARCH,
            params={
                "search": query,
                "per_page": max_results,
                "mailto": "research@example.com"  # Polite pool for better rate limits
            },
            timeout=15,
            headers={"User-Agent": "ResearchPaperAnalyzer/1.0"}
        )
        resp.raise_for_status()
        data = resp.json() or {}
        results = []
        for r in data.get("results", []):
            # Reconstruct abstract from inverted index
            abstract = ""
            inverted_index = r.get("abstract_inverted_index", {})
            if inverted_index:
                # OpenAlex stores abstract as inverted index: {"word": [positions]}
                words_with_positions = []
                for word, positions in inverted_index.items():
                    for pos in positions:
                        words_with_positions.append((pos, word))
                words_with_positions.sort()
                abstract = " ".join(w for _, w in words_with_positions)
            
            results.append({
                "title": r.get("title", "") or r.get("display_name", ""),
                "abstract": abstract,
                "url": r.get("id", ""),
                "source": "OpenAlex"
            })
        return results
    except Exception as e:
        logger.warning(f"OpenAlex search failed: {e}")
        return []


# -------------------- CORE ANALYSIS -------------------- #

# Common academic stop words to filter out
ACADEMIC_STOP_WORDS = {
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
    'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
    'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need',
    'this', 'that', 'these', 'those', 'it', 'its', 'we', 'our', 'their',
    'they', 'them', 'which', 'who', 'whom', 'what', 'where', 'when', 'how',
    'paper', 'study', 'research', 'proposed', 'method', 'approach', 'using',
    'based', 'results', 'show', 'shows', 'shown', 'also', 'however', 'thus',
    'figure', 'table', 'section', 'following', 'provide', 'present', 'work',
    'used', 'use', 'case', 'given', 'describe', 'described', 'introduction',
    'abstract', 'conclusion', 'conclusions', 'related', 'previous', 'other'
}

def build_search_query(text: str) -> str:
    """
    Build a short, effective academic search query
    from section text. Extracts meaningful technical keywords.
    """
    # Extract words (4+ characters, alphabetic)
    words = re.findall(r"[A-Za-z]{4,}", text.lower())
    
    # Filter out stop words and deduplicate
    keywords = []
    seen = set()
    for word in words:
        if word not in ACADEMIC_STOP_WORDS and word not in seen:
            keywords.append(word)
            seen.add(word)
            if len(keywords) >= 10:
                break
    
    return " ".join(keywords)


def search_related_papers(section_text: str, max_results: int = 10) -> List[Dict]:
    """
    Search multiple academic databases for related papers.
    Combines results from IEEE Xplore, Semantic Scholar, and OpenAlex.
    """
    query = build_search_query(section_text)
    if not query:
        logger.warning("Could not build search query from text")
        return []

    logger.info(f"Search query: {query[:80]}...")
    results = []
    seen_titles = set()  # Deduplicate by title

    # 1. IEEE Xplore Search (if API key configured)
    try:
        logger.info("Searching IEEE Xplore...")
        ieee_results = ieee_search(section_text, max_results=max_results)
        logger.info(f"IEEE returned {len(ieee_results)} results")
        for item in ieee_results:
            title = item.get("title", "").lower().strip()
            if title and title not in seen_titles:
                seen_titles.add(title)
                results.append({
                    "title": item.get("title", ""),
                    "abstract": item.get("abstract", ""),
                    "url": item.get("url", ""),
                    "source": "IEEE"
                })
    except Exception as e:
        logger.warning(f"IEEE search failed: {e}")

    # 2. Semantic Scholar Search
    try:
        logger.info("Searching Semantic Scholar...")
        resp = requests.get(
            SEMANTIC_SCHOLAR_SEARCH,
            params={
                "query": query,
                "limit": max_results,
                "fields": "title,abstract,url"
            },
            timeout=15,
            headers={"User-Agent": "ResearchPaperAnalyzer/1.0"}
        )
        logger.info(f"Semantic Scholar response: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            ss_papers = data.get("data", [])
            logger.info(f"Semantic Scholar returned {len(ss_papers)} papers")
            for item in ss_papers:
                title = item.get("title", "").lower().strip()
                if title and title not in seen_titles:
                    seen_titles.add(title)
                    results.append({
                        "title": item.get("title", ""),
                        "abstract": item.get("abstract", "") or "",
                        "url": item.get("url", "") or f"https://www.semanticscholar.org/paper/{item.get('paperId', '')}",
                        "source": "SemanticScholar"
                    })
        elif resp.status_code == 429:
            logger.warning("Semantic Scholar rate limited")
        else:
            logger.warning(f"Semantic Scholar returned {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        logger.warning(f"Semantic Scholar search failed: {e}")

    # 3. OpenAlex Search
    try:
        logger.info("Searching OpenAlex...")
        openalex_results = _openalex_search(query, max_results)
        logger.info(f"OpenAlex returned {len(openalex_results)} results")
        for item in openalex_results:
            title = item.get("title", "").lower().strip()
            if title and title not in seen_titles:
                seen_titles.add(title)
                results.append(item)
    except Exception as e:
        logger.warning(f"OpenAlex search failed: {e}")

    logger.info(f"Found {len(results)} unique papers from all sources")
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
