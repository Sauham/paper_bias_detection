"""
Multi-Provider Bias Analyzer Module

This module provides intelligent bias detection in academic papers using
multiple AI providers (Gemini and OpenRouter) with automatic fallback.
"""

import os
import json
import hashlib
import logging
import time
import requests
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from google import genai
from google.genai import types

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class BiasInstance:
    """Represents a single detected bias instance."""
    type: str
    severity: str  # "low", "moderate", "high"
    excerpt: str
    explanation: str
    suggestion: str
    section: str = ""


@dataclass
class BiasAnalysisResult:
    """Complete bias analysis result for a paper."""
    overall_score: int  # 0-100, lower is better (less biased)
    severity: str  # "low", "moderate", "high"
    summary: str
    biases: List[BiasInstance]
    strengths: List[str]
    error: Optional[str] = None
    provider: Optional[str] = None  # Track which API was used


class BiasAnalysisCache:
    """Simple in-memory cache for bias analysis results."""
    
    def __init__(self, ttl_seconds: int = 3600):
        self._cache: Dict[str, tuple] = {}  # hash -> (result, timestamp)
        self._ttl = ttl_seconds
    
    def _hash_text(self, text: str) -> str:
        """Generate hash for cache key."""
        return hashlib.md5(text.encode()).hexdigest()
    
    def get(self, text: str) -> Optional[BiasAnalysisResult]:
        """Get cached result if available and not expired."""
        key = self._hash_text(text)
        if key in self._cache:
            result, timestamp = self._cache[key]
            if time.time() - timestamp < self._ttl:
                logger.info(f"Cache hit for text hash: {key[:8]}...")
                return result
            else:
                del self._cache[key]
        return None
    
    def set(self, text: str, result: BiasAnalysisResult) -> None:
        """Cache analysis result."""
        key = self._hash_text(text)
        self._cache[key] = (result, time.time())
        logger.info(f"Cached result for text hash: {key[:8]}...")


class BiasAnalyzer:
    """
    Analyzes academic papers for various types of biases using multiple AI providers.
    Supports Gemini and OpenRouter with automatic fallback.
    
    Supported bias types:
    - Confirmation Bias: Language assuming conclusions before evidence
    - Selection Bias: Indicators of non-representative sampling
    - Publication Bias: Overly positive framing, suppressing negative results
    - Funding Bias: Undisclosed conflicts of interest
    - Citation Bias: Selective citing supporting predetermined views
    - Methodology Bias: Flawed experimental design
    """
    
    SYSTEM_PROMPT = """You are an expert academic reviewer specializing in detecting biases in research papers. Your task is to analyze academic text for potential biases that could affect the validity or objectivity of the research.

Analyze the provided text for these bias types:

1. **Confirmation Bias**: Language that assumes conclusions before presenting evidence, or interprets results to fit predetermined beliefs. Look for phrases like "clearly proves", "obviously demonstrates", "as expected".

2. **Selection Bias**: Indicators of non-representative sampling, cherry-picked data, or exclusion criteria that might skew results. Look for limited samples, convenience sampling, or unjustified exclusions.

3. **Publication Bias**: Overly positive framing, suppression of negative or null results, exaggerated claims of novelty or importance. Look for "breakthrough", "revolutionary", "first ever" without justification.

4. **Funding Bias**: Potential conflicts of interest, industry-sponsored research without disclosure, or conclusions that suspiciously align with funder interests.

5. **Citation Bias**: Selective citing that only supports the authors' views, ignoring contradictory evidence, or over-reliance on self-citations.

6. **Methodology Bias**: Flawed experimental design, lack of controls, inappropriate statistical methods, or p-hacking indicators.

For each bias found:
- Quote the EXACT excerpt showing the bias (keep it brief, under 50 characters)
- Rate severity as "low", "moderate", or "high"
- Explain clearly WHY it's biased (1 sentence max)
- Provide a concrete suggestion for improvement (1 sentence max)

Also identify STRENGTHS - good practices the paper follows (e.g., "acknowledges limitations", "uses control group"). Keep strength descriptions brief (under 10 words each).

Calculate an overall bias score from 0-100 where:
- 0-25: Low bias (excellent objectivity)
- 26-50: Moderate bias (some concerns)
- 51-75: High bias (significant issues)
- 76-100: Severe bias (major credibility concerns)

IMPORTANT: 
- Respond ONLY with valid JSON matching this exact schema
- Keep all text fields CONCISE to avoid truncation
- Limit to maximum 5 biases and 5 strengths

{
  "biases": [
    {
      "type": "Confirmation Bias|Selection Bias|Publication Bias|Funding Bias|Citation Bias|Methodology Bias",
      "severity": "low|moderate|high",
      "excerpt": "brief quote",
      "explanation": "one sentence why biased",
      "suggestion": "one sentence fix"
    }
  ],
  "overall_score": 0-100,
  "summary": "1-2 sentence summary",
  "strengths": ["brief strength"]
}

If no biases are found, return an empty "biases" array with a low score and appropriate summary."""

    def __init__(self):
        """Initialize the Bias Analyzer with configured AI provider."""
        self.enabled = os.getenv("BIAS_ANALYSIS_ENABLED", "true").lower() == "true"
        self.provider = os.getenv("AI_PROVIDER", "gemini").lower()
        
        # Initialize Gemini
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        self.gemini_client = None
        
        # Initialize OpenRouter
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY")
        self.openrouter_model = os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-120b:free")
        
        # Initialize cache
        self._cache = BiasAnalysisCache(ttl_seconds=3600)
        
        # Setup primary provider
        if self.provider == "gemini" and self.gemini_key:
            self._init_gemini()
        elif self.provider == "openrouter" and self.openrouter_key:
            logger.info(f"BiasAnalyzer initialized with OpenRouter: {self.openrouter_model}")
        else:
            logger.warning("No valid AI provider configured. Bias analysis will be disabled.")
            self.enabled = False
    
    def _init_gemini(self):
        """Initialize Gemini client."""
        try:
            self.gemini_client = genai.Client(api_key=self.gemini_key)
            logger.info(f"BiasAnalyzer initialized with Gemini: {self.gemini_model}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            self.gemini_client = None

    def _build_prompt(self, text: str, section_name: Optional[str] = None) -> str:
        """Build the analysis prompt."""
        section_context = f"\n\nThis text is from the '{section_name}' section of an academic paper." if section_name else ""
        return f"{self.SYSTEM_PROMPT}{section_context}\n\nText to analyze:\n\"\"\"\n{text}\n\"\"\""

    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Parse and validate the JSON response."""
        try:
            # Clean up response - sometimes AI wraps JSON in markdown
            cleaned = response_text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
            
            data = json.loads(cleaned)
            
            # Validate required fields
            if "biases" not in data:
                data["biases"] = []
            if "overall_score" not in data:
                data["overall_score"] = 50
            if "summary" not in data:
                data["summary"] = "Analysis completed but summary not provided."
            if "strengths" not in data:
                data["strengths"] = []
            
            # Ensure score is in valid range
            data["overall_score"] = max(0, min(100, int(data["overall_score"])))
            
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response: {e}")
            logger.error(f"Response was: {response_text[:500]}...")
            return {
                "biases": [],
                "overall_score": 50,
                "summary": "Failed to parse bias analysis response.",
                "strengths": [],
                "error": str(e)
            }

    def _call_gemini(self, prompt: str) -> tuple[Optional[str], Optional[str]]:
        """
        Call Gemini API.
        Returns: (response_text, error_message)
        """
        if not self.gemini_client or not self.gemini_key:
            return None, "Gemini not initialized"
        
        try:
            response = self.gemini_client.models.generate_content(
                model=self.gemini_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    top_p=0.8,
                    top_k=40,
                    max_output_tokens=8192,
                )
            )
            
            if response and response.text:
                logger.info("✅ Gemini API call successful")
                return response.text, None
            else:
                return None, "Empty response from Gemini"
                
        except Exception as e:
            error_msg = str(e)
            logger.warning(f"Gemini API failed: {error_msg}")
            return None, error_msg

    def _call_openrouter(self, prompt: str) -> tuple[Optional[str], Optional[str]]:
        """
        Call OpenRouter API.
        Returns: (response_text, error_message)
        """
        if not self.openrouter_key:
            return None, "OpenRouter API key not configured"
        
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.openrouter_key}",
                    "HTTP-Referer": "https://github.com/rk0802p/paper_bias_detection",
                    "X-Title": "Paper Bias Detection"
                },
                json={
                    "model": self.openrouter_model,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 8192
                },
                timeout=120
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                if content:
                    logger.info("✅ OpenRouter API call successful")
                    return content, None
                else:
                    return None, "Empty response from OpenRouter"
            else:
                error_msg = f"OpenRouter API error {response.status_code}: {response.text}"
                logger.warning(error_msg)
                return None, error_msg
                
        except Exception as e:
            error_msg = str(e)
            logger.warning(f"OpenRouter API failed: {error_msg}")
            return None, error_msg

    def _determine_severity(self, score: int) -> str:
        """Determine overall severity from score."""
        if score <= 25:
            return "low"
        elif score <= 50:
            return "moderate"
        else:
            return "high"

    def analyze_text(self, text: str, section_name: Optional[str] = None, use_cache: bool = True) -> BiasAnalysisResult:
        """
        Analyze text for biases using configured AI provider with automatic fallback.
        
        Args:
            text: The academic text to analyze
            section_name: Optional name of the section (e.g., "Abstract", "Methodology")
            use_cache: Whether to use cached results
            
        Returns:
            BiasAnalysisResult with detected biases and analysis
        """
        if not self.enabled:
            return BiasAnalysisResult(
                overall_score=0,
                severity="low",
                summary="Bias analysis is disabled. Enable by setting BIAS_ANALYSIS_ENABLED=true.",
                biases=[],
                strengths=[],
                error="Bias analysis disabled",
                provider=None
            )
        
        # Check cache
        if use_cache:
            cached = self._cache.get(text)
            if cached:
                return cached
        
        # Truncate very long texts
        max_chars = 30000
        if len(text) > max_chars:
            logger.warning(f"Text truncated from {len(text)} to {max_chars} characters")
            text = text[:max_chars] + "\n\n[Text truncated for analysis]"
        
        prompt = self._build_prompt(text, section_name)
        response_text = None
        error_msg = None
        provider_used = None
        
        # Try primary provider
        if self.provider == "gemini":
            response_text, error_msg = self._call_gemini(prompt)
            provider_used = "gemini" if response_text else None
            
            # Fallback to OpenRouter if Gemini fails and OpenRouter is available
            if not response_text and self.openrouter_key:
                logger.info("🔄 Falling back to OpenRouter due to Gemini failure")
                response_text, fallback_error = self._call_openrouter(prompt)
                if response_text:
                    provider_used = "openrouter"
                    error_msg = None
                else:
                    error_msg = f"Both providers failed. Gemini: {error_msg}, OpenRouter: {fallback_error}"
        else:
            # Use OpenRouter as primary
            response_text, error_msg = self._call_openrouter(prompt)
            provider_used = "openrouter" if response_text else None
            
            # Fallback to Gemini if OpenRouter fails and Gemini is available
            if not response_text and self.gemini_key and self.gemini_client:
                logger.info("🔄 Falling back to Gemini due to OpenRouter failure")
                response_text, fallback_error = self._call_gemini(prompt)
                if response_text:
                    provider_used = "gemini"
                    error_msg = None
                else:
                    error_msg = f"Both providers failed. OpenRouter: {error_msg}, Gemini: {fallback_error}"
        
        # Handle complete failure
        if not response_text:
            return BiasAnalysisResult(
                overall_score=50,
                severity="moderate",
                summary=f"Analysis failed: {error_msg}",
                biases=[],
                strengths=[],
                error=error_msg,
                provider=None
            )
        
        # Parse response
        data = self._parse_response(response_text)
        
        # Convert to BiasInstance objects
        biases = []
        for b in data.get("biases", []):
            biases.append(BiasInstance(
                type=b.get("type", "Unknown"),
                severity=b.get("severity", "moderate"),
                excerpt=b.get("excerpt", ""),
                explanation=b.get("explanation", ""),
                suggestion=b.get("suggestion", ""),
                section=section_name or ""
            ))
        
        result = BiasAnalysisResult(
            overall_score=data.get("overall_score", 50),
            severity=self._determine_severity(data.get("overall_score", 50)),
            summary=data.get("summary", ""),
            biases=biases,
            strengths=data.get("strengths", []),
            error=data.get("error"),
            provider=provider_used
        )
        
        # Cache the result
        if use_cache and not result.error:
            self._cache.set(text, result)
        
        logger.info(f"✅ Analysis complete using {provider_used}")
        return result

    def analyze_paper_sections(self, sections: Dict[str, str]) -> BiasAnalysisResult:
        """
        Analyze multiple sections of a paper and combine results.
        
        Args:
            sections: Dict mapping section names to their text content
            
        Returns:
            Combined BiasAnalysisResult for the entire paper
        """
        if not self.enabled:
            return BiasAnalysisResult(
                overall_score=0,
                severity="low",
                summary="Bias analysis is disabled.",
                biases=[],
                strengths=[],
                error="Bias analysis disabled",
                provider=None
            )
        
        # Combine all sections into one analysis for efficiency
        combined_text = ""
        for section_name, text in sections.items():
            if text and text.strip():
                combined_text += f"\n\n=== {section_name.upper()} ===\n{text}"
        
        if not combined_text.strip():
            return BiasAnalysisResult(
                overall_score=0,
                severity="low",
                summary="No text provided for analysis.",
                biases=[],
                strengths=[],
                error="Empty input",
                provider=None
            )
        
        return self.analyze_text(combined_text, section_name="Full Paper")


def result_to_dict(result: BiasAnalysisResult) -> Dict[str, Any]:
    """Convert BiasAnalysisResult to a JSON-serializable dictionary."""
    return {
        "overall_score": result.overall_score,
        "severity": result.severity,
        "summary": result.summary,
        "biases": [asdict(b) for b in result.biases],
        "strengths": result.strengths,
        "error": result.error,
        "provider": result.provider
    }


# Backward compatibility
GeminiBiasAnalyzer = BiasAnalyzer


# For testing
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    analyzer = BiasAnalyzer()
    
    test_text = """
    Our groundbreaking study clearly proves that our novel approach significantly 
    outperforms all existing methods. The results obviously demonstrate the 
    superiority of our technique. We selected participants who were likely to 
    respond well to our treatment. As expected, the outcomes confirmed our 
    hypothesis that this revolutionary method is the best solution available.
    The p-value was p=0.049, showing statistical significance.
    """
    
    print("Analyzing test text...")
    result = analyzer.analyze_text(test_text, section_name="Results")
    
    print(f"\nProvider Used: {result.provider}")
    print(f"Overall Score: {result.overall_score}/100")
    print(f"Severity: {result.severity}")
    print(f"Summary: {result.summary}")
    print(f"\nBiases Found: {len(result.biases)}")
    for bias in result.biases:
        print(f"  - {bias.type} ({bias.severity}): {bias.excerpt[:50]}...")
    print(f"\nStrengths: {result.strengths}")
