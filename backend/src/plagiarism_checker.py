import re
import time
import os
import json
import logging
import requests
from typing import Dict, List, Tuple, Optional

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
CROSSREF_SEARCH = "https://api.crossref.org/works"
ARXIV_SEARCH = "http://export.arxiv.org/api/query"

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

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


def _fix_concatenated_text(text: str) -> str:
    """
    Fix text that has concatenated words without spaces.
    Handles camelCase, run-together words, and PDF extraction issues.
    """
    if not text:
        return ""
    
    # 1. Add spaces before capital letters in camelCase (e.g., "deepFake" -> "deep Fake")
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    
    # 2. Add spaces between lowercase and numbers (e.g., "model2" -> "model 2")
    text = re.sub(r'([a-zA-Z])(\d)', r'\1 \2', text)
    text = re.sub(r'(\d)([a-zA-Z])', r'\1 \2', text)
    
    # 3. Fix common concatenation patterns from PDF extraction
    # Pattern: lowercaseUPPERCASE or multiple capitals followed by lowercase
    text = re.sub(r'([a-z]{2,})([A-Z][a-z])', r'\1 \2', text)
    
    # 4. Split on common word boundaries that might be missing spaces
    # Words like "thepaper" -> "the paper"
    common_articles = ['the', 'a', 'an', 'in', 'on', 'of', 'to', 'for', 'and', 'or', 'by', 'with', 'from', 'as', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'this', 'that', 'these', 'those', 'we', 'our', 'their', 'they']
    for article in common_articles:
        # Add space after article if followed by lowercase
        pattern = rf'\b({article})([a-z]{{3,}})'
        text = re.sub(pattern, r'\1 \2', text, flags=re.IGNORECASE)
        # Add space before article if preceded by lowercase
        pattern = rf'([a-z]{{3,}})({article})\b'
        text = re.sub(pattern, r'\1 \2', text, flags=re.IGNORECASE)
    
    # 5. Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


def _retry_request(func, *args, max_retries=MAX_RETRIES, **kwargs):
    """Retry a request with exponential backoff."""
    last_exception = None
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.RequestException as e:
            last_exception = e
            if attempt < max_retries - 1:
                wait_time = RETRY_DELAY * (2 ** attempt)
                logger.info(f"Retry {attempt + 1}/{max_retries} after {wait_time}s...")
                time.sleep(wait_time)
    raise last_exception if last_exception else Exception("Max retries exceeded")


def similarity_percent(a: str, b: str) -> float:
    vectorizer = TfidfVectorizer(stop_words="english")
    try:
        X = vectorizer.fit_transform([a or "", b or ""])
        sim = cosine_similarity(X[0:1], X[1:2]).ravel()[0]
    except ValueError:
        sim = 0.0
    return max(0.0, min(1.0, float(sim))) * 100.0


def categorize_similarity(pct: float) -> str:
    """
    Categorize similarity percentage:
    - 0-10%: Low similarity (mostly original)
    - 10-25%: Moderate similarity (some overlap)
    - >25%: High similarity (review recommended)
    """
    if pct <= 10:
        return "Low similarity"
    if pct <= 25:
        return "Moderate similarity"
    return "High similarity (review recommended)"


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


def _crossref_search(query: str, max_results: int = 10) -> List[Dict]:
    """
    Search CrossRef for academic papers.
    FREE API - No key required!
    CrossRef has 130M+ scholarly works.
    """
    try:
        resp = requests.get(
            CROSSREF_SEARCH,
            params={
                "query": query,
                "rows": max_results,
                "select": "title,abstract,URL,DOI",
                "mailto": "research@example.com"  # Polite pool
            },
            timeout=15,
            headers={"User-Agent": "ResearchPaperAnalyzer/1.0 (mailto:research@example.com)"}
        )
        resp.raise_for_status()
        data = resp.json() or {}
        
        results = []
        items = data.get("message", {}).get("items", [])
        
        for item in items:
            title_list = item.get("title", [])
            title = title_list[0] if title_list else ""
            abstract = item.get("abstract", "") or ""
            # Clean HTML tags from abstract
            abstract = re.sub(r'<[^>]+>', '', abstract)
            url = item.get("URL", "") or f"https://doi.org/{item.get('DOI', '')}"
            
            if title:
                results.append({
                    "title": title,
                    "abstract": abstract,
                    "url": url,
                    "source": "CrossRef"
                })
        
        return results
    except Exception as e:
        logger.warning(f"CrossRef search failed: {e}")
        return []


def _arxiv_search(query: str, max_results: int = 10) -> List[Dict]:
    """
    Search arXiv for academic papers.
    FREE API - No key required!
    Great for CS, Physics, Math papers.
    """
    try:
        # arXiv uses a different query format
        search_query = "+AND+".join(f"all:{word}" for word in query.split()[:5])
        
        resp = requests.get(
            ARXIV_SEARCH,
            params={
                "search_query": search_query,
                "start": 0,
                "max_results": max_results,
                "sortBy": "relevance",
                "sortOrder": "descending"
            },
            timeout=15,
            headers={"User-Agent": "ResearchPaperAnalyzer/1.0"}
        )
        resp.raise_for_status()
        
        # Parse XML response
        import xml.etree.ElementTree as ET
        root = ET.fromstring(resp.content)
        
        # Define namespace
        ns = {
            'atom': 'http://www.w3.org/2005/Atom',
            'arxiv': 'http://arxiv.org/schemas/atom'
        }
        
        results = []
        for entry in root.findall('atom:entry', ns):
            title_elem = entry.find('atom:title', ns)
            title = title_elem.text.strip().replace('\n', ' ') if title_elem is not None else ""
            
            summary_elem = entry.find('atom:summary', ns)
            abstract = summary_elem.text.strip().replace('\n', ' ') if summary_elem is not None else ""
            
            # Get the abstract page link (not PDF)
            url = ""
            for link in entry.findall('atom:link', ns):
                if link.get('type') == 'text/html':
                    url = link.get('href', '')
                    break
            if not url:
                id_elem = entry.find('atom:id', ns)
                url = id_elem.text if id_elem is not None else ""
            
            if title:
                results.append({
                    "title": title,
                    "abstract": abstract,
                    "url": url,
                    "source": "arXiv"
                })
        
        return results
    except Exception as e:
        logger.warning(f"arXiv search failed: {e}")
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
    # First, fix any concatenated text from PDF extraction
    text = _fix_concatenated_text(text)
    
    # Extract words (4+ characters, alphabetic)
    words = re.findall(r"\b[A-Za-z]{4,}\b", text.lower())
    
    # Filter out stop words and deduplicate
    keywords = []
    seen = set()
    for word in words:
        # Skip if it's a stop word or already seen
        if word in ACADEMIC_STOP_WORDS or word in seen:
            continue
        # Skip very long words (likely concatenation errors)
        if len(word) > 20:
            continue
        keywords.append(word)
        seen.add(word)
        if len(keywords) >= 8:  # Keep query focused
            break
    
    query = " ".join(keywords)
    logger.debug(f"Built search query: {query}")
    return query


def _gemini_find_papers(text: str, max_results: int = 5) -> List[Dict]:
    """
    Use Gemini AI to find similar academic papers.
    This is a fallback when other APIs fail or return no results.
    """
    try:
        from google import genai
        from google.genai import types
        
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return []
        
        client = genai.Client(api_key=api_key)
        
        # Extract key concepts from the text
        excerpt = text[:2000]  # Limit text size
        
        prompt = f"""Based on this academic paper excerpt, identify 5 real, published academic papers that discuss similar topics or methodologies. 

Paper excerpt:
{excerpt}

Return ONLY a JSON array of papers with this exact format (no markdown, no explanation):
[
  {{"title": "Exact Paper Title", "authors": "Author Names", "year": "2023", "url": "https://doi.org/..."}},
  ...
]

Requirements:
- Only include real, verifiable papers that actually exist
- Include DOI links when possible
- Focus on papers from major publishers (IEEE, ACM, Springer, Nature, arXiv)
- Return exactly 5 papers"""

        response = client.models.generate_content(
            model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,  # Low temperature for factual responses
                max_output_tokens=1000
            )
        )
        
        # Parse the JSON response
        response_text = response.text.strip()
        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            response_text = re.sub(r'^```\w*\n?', '', response_text)
            response_text = re.sub(r'\n?```$', '', response_text)
        
        papers = json.loads(response_text)
        
        results = []
        for paper in papers[:max_results]:
            title = paper.get("title", "")
            if title:
                results.append({
                    "title": title,
                    "abstract": f"By {paper.get('authors', 'Unknown')} ({paper.get('year', '')})",
                    "url": paper.get("url", ""),
                    "source": "Gemini"
                })
        
        return results
    except Exception as e:
        logger.warning(f"Gemini paper search failed: {e}")
        return []


def search_related_papers(section_text: str, max_results: int = 10) -> List[Dict]:
    """
    Search multiple academic databases for related papers.
    Combines results from CrossRef, arXiv, Semantic Scholar, OpenAlex, IEEE, and Gemini.
    """
    # Fix concatenated text first
    fixed_text = _fix_concatenated_text(section_text)
    query = build_search_query(fixed_text)
    
    if not query:
        logger.warning("Could not build search query from text")
        return []

    logger.info(f"Search query: '{query}'")
    results = []
    seen_titles = set()  # Deduplicate by title
    
    def add_results(items: List[Dict], source_name: str):
        """Helper to add results with deduplication."""
        added = 0
        for item in items:
            title = item.get("title", "").lower().strip()
            if title and len(title) > 10 and title not in seen_titles:
                seen_titles.add(title)
                results.append(item)
                added += 1
        return added

    # 1. CrossRef Search (FREE, no key needed, largest database)
    try:
        logger.info("Searching CrossRef...")
        crossref_results = _crossref_search(query, max_results)
        added = add_results(crossref_results, "CrossRef")
        logger.info(f"CrossRef returned {len(crossref_results)} results, added {added} unique")
    except Exception as e:
        logger.warning(f"CrossRef search failed: {e}")

    # 2. arXiv Search (FREE, no key needed, great for CS/ML papers)
    try:
        logger.info("Searching arXiv...")
        arxiv_results = _arxiv_search(query, max_results)
        added = add_results(arxiv_results, "arXiv")
        logger.info(f"arXiv returned {len(arxiv_results)} results, added {added} unique")
    except Exception as e:
        logger.warning(f"arXiv search failed: {e}")

    # 3. OpenAlex Search (FREE, no key needed)
    try:
        logger.info("Searching OpenAlex...")
        openalex_results = _openalex_search(query, max_results)
        added = add_results(openalex_results, "OpenAlex")
        logger.info(f"OpenAlex returned {len(openalex_results)} results, added {added} unique")
    except Exception as e:
        logger.warning(f"OpenAlex search failed: {e}")

    # 4. Semantic Scholar Search (FREE, but rate limited)
    try:
        logger.info("Searching Semantic Scholar...")
        for attempt in range(2):  # Retry once if rate limited
            resp = requests.get(
                SEMANTIC_SCHOLAR_SEARCH,
                params={
                    "query": query,
                    "limit": max_results,
                    "fields": "title,abstract,url,paperId"
                },
                timeout=15,
                headers={"User-Agent": "ResearchPaperAnalyzer/1.0"}
            )
            
            if resp.status_code == 200:
                data = resp.json()
                ss_papers = data.get("data", [])
                ss_results = []
                for item in ss_papers:
                    ss_results.append({
                        "title": item.get("title", ""),
                        "abstract": item.get("abstract", "") or "",
                        "url": item.get("url", "") or f"https://www.semanticscholar.org/paper/{item.get('paperId', '')}",
                        "source": "SemanticScholar"
                    })
                added = add_results(ss_results, "SemanticScholar")
                logger.info(f"Semantic Scholar returned {len(ss_papers)} results, added {added} unique")
                break
            elif resp.status_code == 429:
                logger.warning(f"Semantic Scholar rate limited, attempt {attempt + 1}")
                if attempt == 0:
                    time.sleep(2)  # Wait before retry
            else:
                logger.warning(f"Semantic Scholar returned {resp.status_code}")
                break
    except Exception as e:
        logger.warning(f"Semantic Scholar search failed: {e}")

    # 5. IEEE Xplore Search (requires API key)
    try:
        logger.info("Searching IEEE Xplore...")
        ieee_results = ieee_search(fixed_text, max_results=max_results)
        added = add_results([{
            "title": item.get("title", ""),
            "abstract": item.get("abstract", ""),
            "url": item.get("url", ""),
            "source": "IEEE"
        } for item in ieee_results], "IEEE")
        logger.info(f"IEEE returned {len(ieee_results)} results, added {added} unique")
    except Exception as e:
        logger.warning(f"IEEE search failed: {e}")

    # 6. Gemini AI Fallback (if we have few results)
    if len(results) < 5:
        try:
            logger.info("Using Gemini AI to find additional papers...")
            gemini_results = _gemini_find_papers(fixed_text, max_results=5)
            added = add_results(gemini_results, "Gemini")
            logger.info(f"Gemini found {len(gemini_results)} papers, added {added} unique")
        except Exception as e:
            logger.warning(f"Gemini search failed: {e}")

    logger.info(f"Total: Found {len(results)} unique papers from all sources")
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
