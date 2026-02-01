"""
IEEE Xplore API Integration Module

This module provides integration with the IEEE Xplore Metadata API for searching
academic papers and retrieving metadata including abstracts, titles, and citations.

API Documentation: https://developer.ieee.org/docs
"""

import os
import re
import logging
from typing import List, Dict, Optional, Any
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# IEEE Xplore API configuration
IEEE_API_KEY = os.getenv("IEEE_API_KEY")
IEEE_BASE_URL = "https://ieeexploreapi.ieee.org/api/v1/search/articles"


def _extract_keywords(text: str, max_words: int = 8) -> str:
    """
    Extract meaningful keywords from text for search query.
    Filters out common words and keeps technical terms.
    """
    # Common words to filter out
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
        'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need',
        'this', 'that', 'these', 'those', 'it', 'its', 'we', 'our', 'their',
        'they', 'them', 'which', 'who', 'whom', 'what', 'where', 'when', 'how',
        'paper', 'study', 'research', 'proposed', 'method', 'approach', 'using',
        'based', 'results', 'show', 'shows', 'shown', 'also', 'however', 'thus'
    }
    
    # Extract words (4+ characters, alphabetic)
    words = re.findall(r'\b[A-Za-z]{4,}\b', text.lower())
    
    # Filter and deduplicate
    keywords = []
    seen = set()
    for word in words:
        if word not in stop_words and word not in seen:
            keywords.append(word)
            seen.add(word)
            if len(keywords) >= max_words:
                break
    
    return ' '.join(keywords)


def _build_boolean_query(text: str) -> str:
    """
    Build a simple search query for IEEE API.
    Keep it simple - IEEE works better with fewer, relevant terms.
    """
    keywords = _extract_keywords(text, max_words=5)
    if not keywords:
        return ""
    
    # IEEE API works better with simple space-separated terms
    return keywords


def ieee_search(
    section_text: str,
    max_results: int = 10,
    content_types: Optional[List[str]] = None,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Search IEEE Xplore for papers related to the given text.
    
    Args:
        section_text: Text content to search for (abstract, methodology, etc.)
        max_results: Maximum number of results to return (max 200 per API)
        content_types: List of content types to filter 
                      (e.g., ["Journals", "Conferences", "Standards"])
        start_year: Filter results from this year onwards
        end_year: Filter results up to this year
    
    Returns:
        List of dictionaries containing paper metadata:
        - title: Paper title
        - abstract: Paper abstract
        - url: Link to paper on IEEE Xplore
        - authors: List of author names
        - publication_title: Journal/Conference name
        - publication_year: Year published
        - doi: Digital Object Identifier
        - citing_paper_count: Number of citations
        - source: Always "IEEE"
    """
    if not IEEE_API_KEY:
        logger.warning("IEEE_API_KEY not configured. IEEE search disabled.")
        return []
    
    if not section_text or len(section_text.strip()) < 20:
        logger.warning("Section text too short for meaningful search")
        return []
    
    # Build search query
    query = _build_boolean_query(section_text)
    if not query:
        logger.warning("Could not extract meaningful keywords from text")
        return []
    
    logger.info(f"IEEE search query: {query[:100]}...")
    
    # Build API parameters based on IEEE documentation
    # Keep parameters simple for better results
    params = {
        "apikey": IEEE_API_KEY,
        "format": "json",
        "max_records": min(max_results, 25),  # Keep it small for speed
        "start_record": 1,
        "querytext": query,  # Free-text search across metadata and abstract
    }
    
    # Only add filters if explicitly specified (avoid over-filtering)
    if content_types and len(content_types) > 0:
        params["content_type"] = ",".join(content_types)
    
    if start_year:
        params["start_year"] = start_year
    if end_year:
        params["end_year"] = end_year
    
    logger.info(f"IEEE API params: {params}")
    
    try:
        response = requests.get(
            IEEE_BASE_URL,
            params=params,
            timeout=20,
            headers={"Accept": "application/json"}
        )
        response.raise_for_status()
        data = response.json()
        
    except requests.exceptions.Timeout:
        logger.error("IEEE API request timed out")
        return []
    except requests.exceptions.RequestException as e:
        logger.error(f"IEEE API request failed: {e}")
        return []
    except ValueError as e:
        logger.error(f"Failed to parse IEEE API response: {e}")
        return []
    
    # Parse results
    results = []
    articles = data.get("articles", [])
    total_found = data.get("total_records", 0)
    
    logger.info(f"IEEE search found {total_found} total results, returning {len(articles)}")
    
    for article in articles:
        # Extract author names
        authors = []
        for author in article.get("authors", {}).get("authors", []):
            full_name = author.get("full_name", "")
            if full_name:
                authors.append(full_name)
        
        # Build URL - prefer abstract URL, fall back to PDF/HTML
        url = (
            article.get("abstract_url") or
            article.get("html_url") or
            article.get("pdf_url") or
            f"https://ieeexplore.ieee.org/document/{article.get('article_number', '')}"
        )
        
        results.append({
            "title": article.get("title", "Unknown Title"),
            "abstract": article.get("abstract", ""),
            "url": url,
            "authors": authors,
            "publication_title": article.get("publication_title", ""),
            "publication_year": article.get("publication_year", ""),
            "doi": article.get("doi", ""),
            "citing_paper_count": article.get("citing_paper_count", 0),
            "content_type": article.get("content_type", ""),
            "publisher": article.get("publisher", "IEEE"),
            "source": "IEEE"
        })
    
    return results


def ieee_search_by_doi(doi: str) -> Optional[Dict[str, Any]]:
    """
    Search IEEE Xplore by DOI for exact paper match.
    
    Args:
        doi: Digital Object Identifier (e.g., "10.1109/ACCESS.2021.3068614")
    
    Returns:
        Paper metadata dict or None if not found
    """
    if not IEEE_API_KEY:
        return None
    
    if not doi:
        return None
    
    params = {
        "apikey": IEEE_API_KEY,
        "format": "json",
        "doi": doi
    }
    
    try:
        response = requests.get(IEEE_BASE_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        articles = data.get("articles", [])
        if articles:
            article = articles[0]
            return {
                "title": article.get("title", ""),
                "abstract": article.get("abstract", ""),
                "url": article.get("abstract_url") or article.get("html_url", ""),
                "doi": article.get("doi", ""),
                "source": "IEEE"
            }
    except Exception as e:
        logger.error(f"IEEE DOI search failed: {e}")
    
    return None


def ieee_search_by_title(title: str, exact_match: bool = False) -> List[Dict[str, Any]]:
    """
    Search IEEE Xplore by article title.
    
    Args:
        title: Article title to search for
        exact_match: If True, search for exact title match
    
    Returns:
        List of matching papers
    """
    if not IEEE_API_KEY:
        return []
    
    if not title or len(title.strip()) < 5:
        return []
    
    # Clean title for search
    clean_title = re.sub(r'[^\w\s]', ' ', title)
    clean_title = ' '.join(clean_title.split()[:15])  # Limit to first 15 words
    
    params = {
        "apikey": IEEE_API_KEY,
        "format": "json",
        "max_records": 5,
        "article_title": clean_title
    }
    
    try:
        response = requests.get(IEEE_BASE_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for article in data.get("articles", []):
            results.append({
                "title": article.get("title", ""),
                "abstract": article.get("abstract", ""),
                "url": article.get("abstract_url") or article.get("html_url", ""),
                "doi": article.get("doi", ""),
                "publication_year": article.get("publication_year", ""),
                "source": "IEEE"
            })
        return results
        
    except Exception as e:
        logger.error(f"IEEE title search failed: {e}")
        return []


def check_ieee_api_status() -> Dict[str, Any]:
    """
    Check if IEEE API is configured and accessible.
    
    Returns:
        Status dict with 'available', 'message', and 'api_key_configured' fields
    """
    status = {
        "available": False,
        "api_key_configured": bool(IEEE_API_KEY),
        "message": ""
    }
    
    if not IEEE_API_KEY:
        status["message"] = "IEEE_API_KEY not configured in environment"
        return status
    
    try:
        # Simple test query
        params = {
            "apikey": IEEE_API_KEY,
            "format": "json",
            "max_records": 1,
            "querytext": "machine learning"
        }
        response = requests.get(IEEE_BASE_URL, params=params, timeout=10)
        
        if response.status_code == 200:
            status["available"] = True
            status["message"] = "IEEE API is accessible"
        elif response.status_code == 403:
            status["message"] = "IEEE API key is invalid or expired"
        else:
            status["message"] = f"IEEE API returned status {response.status_code}"
            
    except Exception as e:
        status["message"] = f"Failed to connect to IEEE API: {str(e)}"
    
    return status
