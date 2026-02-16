import re
import time
import os
import json
import logging
import requests
from typing import Dict, List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

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
RETRY_DELAY = 1  # seconds (exponential backoff: 1s, 2s, then fail)
SEMANTIC_SCHOLAR_WAIT = 4  # seconds between retries (rate limit: 1 req per 3.5s without API key)

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

# Try to load spaCy - graceful fallback if not installed
try:
    import spacy
    try:
        _nlp = spacy.load("en_core_web_sm")
        SPACY_AVAILABLE = True
    except OSError:
        # Model not downloaded yet
        SPACY_AVAILABLE = False
        _nlp = None
except ImportError:
    SPACY_AVAILABLE = False
    _nlp = None


def _extract_sections_regex(text: str) -> dict:
    """
    Enhanced regex-based section extraction.
    Handles section numbers (1., I., A., 1.1) and many naming variations.
    """
    text = text.replace("\r", "\n")
    lower = text.lower()
    
    # Enhanced patterns with section numbers and more variations
    # Format: (category, pattern) - patterns include optional section numbers
    section_patterns = [
        # Abstract patterns
        ("Abstract", r"(?:^|\n)\s*(?:\d+\.?\s*|[IVX]+\.?\s*|[A-Z]\.?\s*)?(?:abstract)\s*[:\.\n]", re.IGNORECASE | re.MULTILINE),
        
        # Methodology/Methods patterns - many variations
        ("Methodology", r"(?:^|\n)\s*(?:\d+\.?\s*|[IVX]+\.?\s*|[A-Z]\.?\s*)?(?:methodology|methods?|materials?\s+and\s+methods?|approach|proposed\s+(?:system|method|approach|framework|architecture)|system\s+(?:design|architecture|overview)|implementation|experimental\s+(?:setup|design)|technical\s+approach|our\s+approach|framework|design)\s*[:\.\n]", re.IGNORECASE | re.MULTILINE),
        
        # Conclusions patterns
        ("Conclusions", r"(?:^|\n)\s*(?:\d+\.?\s*|[IVX]+\.?\s*|[A-Z]\.?\s*)?(?:conclusions?|discussion|summary|concluding\s+remarks?|final\s+remarks?)\s*[:\.\n]", re.IGNORECASE | re.MULTILINE),
        
        # Introduction (useful for finding paper start)
        ("Introduction", r"(?:^|\n)\s*(?:\d+\.?\s*|[IVX]+\.?\s*|[A-Z]\.?\s*)?(?:introduction)\s*[:\.\n]", re.IGNORECASE | re.MULTILINE),
    ]
    
    # Find all section matches with their positions
    found_sections = []
    for category, pattern, flags in section_patterns:
        for match in re.finditer(pattern, text, flags):
            found_sections.append({
                "category": category,
                "start": match.start(),
                "end": match.end(),
                "match_text": match.group().strip()
            })
    
    # Sort by position in document
    found_sections.sort(key=lambda x: x["start"])
    
    # Extract content between sections
    sections = {}
    for i, section in enumerate(found_sections):
        category = section["category"]
        start = section["end"]  # Start after the header
        
        # End at next section or document end
        if i + 1 < len(found_sections):
            end = found_sections[i + 1]["start"]
        else:
            end = len(text)
        
        content = text[start:end].strip()
        
        # Keep the longest content for each category
        if category not in sections or len(content) > len(sections[category]):
            sections[category] = content
    
    # Extract title from first non-empty line
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    title = lines[0][:200] if lines else ""
    
    return {
        "Title": title,
        "Abstract": sections.get("Abstract", ""),
        "Methodology": sections.get("Methodology", ""),
        "Conclusions": sections.get("Conclusions", ""),
        "confidence": "regex"
    }


def _extract_sections_spacy(text: str) -> dict:
    """
    spaCy-based section extraction using NLP.
    Detects section headers based on linguistic patterns.
    """
    if not SPACY_AVAILABLE or _nlp is None:
        return {"Title": "", "Abstract": "", "Methodology": "", "Conclusions": "", "confidence": "spacy_unavailable"}
    
    # Process with spaCy (limit text length for speed)
    max_chars = 50000  # ~12-15 pages
    doc = _nlp(text[:max_chars])
    
    # Section header keywords for each category
    section_keywords = {
        "Abstract": {"abstract", "summary"},
        "Methodology": {
            "methodology", "methods", "method", "approach", "implementation",
            "proposed", "system", "framework", "architecture", "design",
            "experimental", "setup", "technique", "algorithm", "model"
        },
        "Conclusions": {
            "conclusion", "conclusions", "discussion", "summary",
            "concluding", "remarks", "future"
        },
        "Introduction": {"introduction", "background", "overview"}
    }
    
    # Find potential section headers (short sentences at start of paragraphs)
    sections = {}
    current_section = None
    current_content = []
    
    for sent in doc.sents:
        sent_text = sent.text.strip()
        sent_lower = sent_text.lower()
        
        # Check if this looks like a section header
        is_header = False
        header_category = None
        
        # Header heuristics:
        # 1. Short (< 10 words)
        # 2. Contains section keyword
        # 3. Often starts with number or is ALL CAPS
        words = sent_text.split()
        if len(words) <= 10:
            # Check for section keywords
            for category, keywords in section_keywords.items():
                if any(kw in sent_lower for kw in keywords):
                    # Additional checks: starts with number or has section-like pattern
                    if (re.match(r'^[\d\.]+\s', sent_text) or  # Starts with "1.", "1.1", etc.
                        re.match(r'^[IVX]+\.?\s', sent_text) or  # Roman numerals
                        re.match(r'^[A-Z]\.?\s', sent_text) or  # Letter sections
                        sent_text.isupper() or  # ALL CAPS
                        len(words) <= 5):  # Very short = likely header
                        is_header = True
                        header_category = category
                        break
        
        if is_header and header_category:
            # Save previous section content
            if current_section and current_content:
                content = " ".join(current_content)
                if current_section not in sections or len(content) > len(sections[current_section]):
                    sections[current_section] = content
            
            # Start new section
            current_section = header_category
            current_content = []
        elif current_section:
            current_content.append(sent_text)
    
    # Save last section
    if current_section and current_content:
        content = " ".join(current_content)
        if current_section not in sections or len(content) > len(sections[current_section]):
            sections[current_section] = content
    
    # Extract title
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    title = lines[0][:200] if lines else ""
    
    return {
        "Title": title,
        "Abstract": sections.get("Abstract", ""),
        "Methodology": sections.get("Methodology", ""),
        "Conclusions": sections.get("Conclusions", ""),
        "confidence": "spacy"
    }


def extract_sections(text: str) -> dict:
    """
    Hybrid section extraction using both enhanced regex and spaCy IN PARALLEL.
    Combines results for best accuracy.
    """
    if not text:
        return {
            "Title": "",
            "Abstract": "",
            "Methodology": "",
            "Conclusions": ""
        }
    
    # Run both extractors in parallel
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    results = {}
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {
            executor.submit(_extract_sections_regex, text): "regex",
            executor.submit(_extract_sections_spacy, text): "spacy"
        }
        
        for future in as_completed(futures, timeout=5):
            method = futures[future]
            try:
                results[method] = future.result()
            except Exception as e:
                logger.warning(f"Section extraction ({method}) failed: {e}")
                results[method] = {"Title": "", "Abstract": "", "Methodology": "", "Conclusions": ""}
    
    regex_result = results.get("regex", {})
    spacy_result = results.get("spacy", {})
    
    # Merge results: prefer longer, non-empty content
    def best_content(key):
        regex_val = regex_result.get(key, "")
        spacy_val = spacy_result.get(key, "")
        
        # If one is empty, use the other
        if not regex_val:
            return spacy_val
        if not spacy_val:
            return regex_val
        
        # Both have content - prefer longer one (more complete extraction)
        # But penalize if it looks like garbage (too many truncated words)
        def quality_score(content):
            words = content.split()
            if len(words) < 10:
                return 0
            # Check for truncated words (rough heuristic)
            truncated = sum(1 for w in words[:50] if len(w) > 2 and not w[0].isupper() and w[0] not in 'aeiou')
            return len(content) - (truncated * 10)
        
        return regex_val if quality_score(regex_val) >= quality_score(spacy_val) else spacy_val
    
    final_sections = {
        "Title": regex_result.get("Title") or spacy_result.get("Title", ""),
        "Abstract": best_content("Abstract"),
        "Methodology": best_content("Methodology"),
        "Conclusions": best_content("Conclusions")
    }
    
    # Fallbacks if sections are still empty or too short
    min_length = 100
    
    if len(final_sections["Abstract"]) < min_length:
        # Try to find abstract in first 2000 chars
        abstract_match = re.search(r'abstract[:\.\s]*(.{100,2000}?)(?=\n\s*\n|\n\s*\d+\.|\n\s*[IVX]+\.|\n\s*introduction)', 
                                    text[:3000], re.IGNORECASE | re.DOTALL)
        if abstract_match:
            final_sections["Abstract"] = abstract_match.group(1).strip()
        else:
            final_sections["Abstract"] = text[:1500]
    
    if len(final_sections["Methodology"]) < min_length:
        final_sections["Methodology"] = text[1500:6000]
    
    if len(final_sections["Conclusions"]) < min_length:
        final_sections["Conclusions"] = text[-2500:]
    
    logger.debug(f"Section extraction - Abstract: {len(final_sections['Abstract'])} chars, "
                 f"Methodology: {len(final_sections['Methodology'])} chars, "
                 f"Conclusions: {len(final_sections['Conclusions'])} chars")
    
    return final_sections

# -------------------- SEARCH PROVIDERS -------------------- #

def _semantic_scholar_search(query: str, max_results: int) -> List[Dict]:
    try:
        resp = requests.get(
            SEMANTIC_SCHOLAR_SEARCH,
            params={"query": query, "limit": max_results, "fields": "title,url,abstract"},
            timeout=8
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
            timeout=8,
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
            timeout=8,
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
            timeout=8,
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

def is_likely_truncated(word: str) -> bool:
    """
    Detect if a word is likely truncated from PDF extraction.
    Returns True if the word appears to be malformed/truncated.
    """
    if len(word) < 4:
        return True
    
    word = word.lower()
    
    # Known truncated words from PDF extraction (missing first letter(s))
    truncated_patterns = {
        # Missing 'a' prefix
        'bstract', 'nalysis', 'pproach', 'lgorithm', 'udio', 'reas', 'uthenticity',
        'uthor', 'rticle', 'cademic', 'ccuracy', 'chieve', 'dvanced',
        # Missing 'in' prefix  
        'ternational', 'terdisciplinary', 'troduction', 'vestigation', 'telligent',
        'formation', 'cluding', 'crease', 'creasing', 'ternet', 'tegrates', 'tegrate',
        'tegrated', 'tegration', 'terface', 'terfaces', 'teractive', 'teresting',
        # Missing 'con' prefix
        'clusion', 'conclusi', 'cluded', 'ference', 'tribution', 'sidering',
        # Missing 'de' prefix
        'tection', 'detecti', 'velop', 'velopment', 'tector', 'tected', 'epfake',
        # Missing 're' prefix
        'sults', 'search', 'searc', 'cognition', 'liable', 'levant',
        # Missing 'ex' prefix
        'periment', 'perimental', 'traction', 'plore', 'isting',
        # Missing 'me' prefix
        'thods', 'thodology', 'thod',
        # Missing 'or' prefix
        'iginality', 'iginal',
        # Missing other prefixes
        'udio', 'ignal', 'ignals', 'ystem', 'ystems', 'ection', 'ections',
        'pplication', 'fficient', 'fficiency', 'valuate', 'valuation',
        'roposed', 'resent', 'resented', 'erformance', 'earning',
    }
    
    # Check exact matches
    if word in truncated_patterns:
        return True
    
    # Words ending in incomplete suffixes (likely cut off)
    incomplete_suffixes = ('ti', 'si', 'ri', 'di', 'ni', 'gi', 'ci', 'cti', 'ndi')
    if word.endswith(incomplete_suffixes) and len(word) > 4:
        return True
    
    # Invalid word starts - consonant clusters that don't occur at word beginnings
    invalid_starts = {
        'bstr', 'bsc', 'ppr', 'ntr', 'ncl', 'nst', 'nth', 'xpl', 'xtr', 'xpr',
        'bs', 'bt', 'ck', 'ct', 'dl', 'dm', 'dn', 'ds', 'dt', 'dv',
        'fs', 'ft', 'gm', 'gn', 'gt', 'hm', 'hn', 'hr', 'hs', 'ht',
        'lb', 'lc', 'ld', 'lf', 'lg', 'lk', 'll', 'lm', 'ln', 'lp', 'lr', 'ls', 'lt',
        'mb', 'mc', 'md', 'mf', 'mg', 'mk', 'ml', 'mm', 'mn', 'mp', 'mr', 'ms', 'mt',
        'nb', 'nc', 'nd', 'nf', 'ng', 'nk', 'nl', 'nm', 'nn', 'np', 'nr', 'ns', 'nt', 'nv',
        'pb', 'pc', 'pd', 'pf', 'pg', 'pk', 'pm', 'pn', 'pp', 'pt', 'pv',
        'rb', 'rc', 'rd', 'rf', 'rg', 'rk', 'rl', 'rm', 'rn', 'rp', 'rr', 'rs', 'rt', 'rv',
        'sb', 'sd', 'sf', 'sg', 'sr', 'ss', 'sv',
        'tb', 'tc', 'td', 'tf', 'tg', 'tk', 'tl', 'tm', 'tn', 'tp', 'ts', 'tt', 'tv',
        'vb', 'vc', 'vd', 'vf', 'vg', 'vk', 'vl', 'vm', 'vn', 'vp', 'vr', 'vs', 'vt',
        'wb', 'wc', 'wd', 'wf', 'wg', 'wk', 'wl', 'wm', 'wp', 'ws', 'wt',
        'xb', 'xc', 'xd', 'xf', 'xg', 'xk', 'xl', 'xm', 'xn', 'xp', 'xr', 'xs', 'xt',
        'thm', 'thn', 'ths', 'rch', 'rth', 'lst', 'rst', 'ngl', 'ngs', 'ncr',
    }
    
    # Check first 2-4 characters against invalid starts
    for length in [4, 3, 2]:
        if len(word) >= length and word[:length] in invalid_starts:
            return True
    
    return False


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
        # Skip very long words (likely concatenated garbage from PDF extraction)
        if len(word) > 15:
            logger.debug(f"Skipping long word: '{word[:20]}...'")
            continue
        # Skip truncated words
        if is_likely_truncated(word):
            logger.debug(f"Skipping likely truncated word: '{word}'")
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
    Search multiple academic databases for related papers IN PARALLEL.
    Combines results from CrossRef, arXiv, Semantic Scholar, OpenAlex.
    IEEE is skipped if API key is invalid. Gemini used as fallback.
    """
    # Fix concatenated text first
    fixed_text = _fix_concatenated_text(section_text)
    query = build_search_query(fixed_text)
    
    if not query:
        logger.warning("Could not build search query from text")
        return []

    logger.info(f"Search query: '{query}'")
    all_results = []
    
    # Define search functions for parallel execution
    def search_crossref():
        try:
            results = _crossref_search(query, max_results)
            logger.info(f"CrossRef returned {len(results)} results")
            return results
        except Exception as e:
            logger.warning(f"CrossRef search failed: {e}")
            return []
    
    def search_arxiv():
        try:
            results = _arxiv_search(query, max_results)
            logger.info(f"arXiv returned {len(results)} results")
            return results
        except Exception as e:
            logger.warning(f"arXiv search failed: {e}")
            return []
    
    def search_openalex():
        try:
            results = _openalex_search(query, max_results)
            logger.info(f"OpenAlex returned {len(results)} results")
            return results
        except Exception as e:
            logger.warning(f"OpenAlex search failed: {e}")
            return []
    
    def search_semantic_scholar():
        """Search Semantic Scholar - skip retry if rate limited (too slow)."""
        try:
            resp = requests.get(
                SEMANTIC_SCHOLAR_SEARCH,
                params={
                    "query": query,
                    "limit": max_results,
                    "fields": "title,abstract,url,paperId"
                },
                timeout=8,  # Shorter timeout
                headers={"User-Agent": "ResearchPaperAnalyzer/1.0"}
            )
            
            if resp.status_code == 200:
                data = resp.json()
                ss_papers = data.get("data", [])
                results = []
                for item in ss_papers:
                    results.append({
                        "title": item.get("title", ""),
                        "abstract": item.get("abstract", "") or "",
                        "url": item.get("url", "") or f"https://www.semanticscholar.org/paper/{item.get('paperId', '')}",
                        "source": "SemanticScholar"
                    })
                logger.info(f"Semantic Scholar returned {len(ss_papers)} results")
                return results
            elif resp.status_code == 429:
                logger.warning("Semantic Scholar rate limited, skipping")
                return []
            else:
                logger.warning(f"Semantic Scholar returned {resp.status_code}")
                return []
        except Exception as e:
            logger.warning(f"Semantic Scholar search failed: {e}")
            return []
    
    # Run searches IN PARALLEL using ThreadPoolExecutor
    search_functions = [
        ("CrossRef", search_crossref),
        ("arXiv", search_arxiv),
        ("OpenAlex", search_openalex),
        ("SemanticScholar", search_semantic_scholar),
    ]
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        future_to_source = {
            executor.submit(func): name 
            for name, func in search_functions
        }
        
        for future in as_completed(future_to_source, timeout=15):
            source = future_to_source[future]
            try:
                results = future.result()
                all_results.extend(results)
            except Exception as e:
                logger.warning(f"{source} search failed: {e}")
    
    # Deduplicate results by title
    seen_titles = set()
    unique_results = []
    for item in all_results:
        title = item.get("title", "").lower().strip()
        if title and len(title) > 10 and title not in seen_titles:
            seen_titles.add(title)
            unique_results.append(item)
    
    # Gemini AI Fallback (if we have few results)
    if len(unique_results) < 5:
        try:
            logger.info("Using Gemini AI to find additional papers...")
            gemini_results = _gemini_find_papers(fixed_text, max_results=5)
            for item in gemini_results:
                title = item.get("title", "").lower().strip()
                if title and len(title) > 10 and title not in seen_titles:
                    seen_titles.add(title)
                    unique_results.append(item)
            logger.info(f"Gemini found {len(gemini_results)} papers")
        except Exception as e:
            logger.warning(f"Gemini search failed: {e}")

    logger.info(f"Total: Found {len(unique_results)} unique papers")
    return unique_results

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
