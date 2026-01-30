Research Paper Plagiarism & Bias Detection System

Change Log & Architecture Evolution

🔖 Overview

This document tracks the major changes, fixes, and architectural decisions made during the development and stabilization of the Research Paper Plagiarism & Bias Analysis system.

The goal of these changes was to:

Restore frontend compatibility

Fix backend data contracts

Improve robustness of PDF text extraction

Enable (and safely disable) AI-based bias detection

Make the system demo-ready and stable

✅ Phase 1: Backend Stabilization
1. Fixed Python Indentation & Import Errors

Issues encountered

TabError: inconsistent use of tabs and spaces

NameError due to missing imports

Hot-reload masking stale imports

Fixes

Converted all files to spaces-only indentation

Ensured all imports used correct module paths (src.*)

Restarted Uvicorn cleanly after structural changes

2. Resolved metadata Dependency Errors

Issue

Legacy references to metadata caused runtime failures

extract_metadata() was removed but still referenced

Fix

Completely removed metadata from:

analyze_plagiarism

analyze_section

Simplified plagiarism logic to text-only similarity, improving stability

✅ Phase 2: Plagiarism Detection Pipeline Fixes
3. Fixed Section Extraction Logic

Issue

extract_sections() did not always return expected keys

Missing "Title" caused frontend rendering issues

Fix

Rewrote extract_sections() to always return:

Title

Abstract

Methodology

Conclusions

Added strong fallback slicing for scanned/poor PDFs

4. Restored Section Text in Plagiarism Results

Critical Bug

Frontend only showed section headers (e.g., “Title”) with no content

Root Cause

analyze_plagiarism() returned similarity scores without section text

Fix

Updated analyze_plagiarism() to include:

{
  "text": "...",
  "best_similarity_percent": ...,
  "category": "...",
  "matches": [...]
}


This restored full frontend rendering without frontend changes.

5. Fixed Overall vs Section Percentage Mismatch

Issue

Overall plagiarism score (e.g., 14.8%) displayed

Individual sections showed 0%

Cause

API returned raw extracted sections instead of analyzed sections

Fix

API now returns:

plagiarism_report["sections"]


instead of:

extract_sections(full_text)


This aligned frontend display with backend calculations.

✅ Phase 3: Search & Similarity Improvements
6. Added Proper Academic Search Query Builder

Issue

Long section text sent directly to Semantic Scholar

Resulted in zero matches

Fix

Introduced build_search_query():

Extracts top meaningful keywords

Limits query length

Dramatically improved match discovery

7. Added Defensive Similarity Handling

Fixes

Guaranteed numeric similarity output (0.0 fallback)

Prevented % display without numbers

Ensured demo-safe behavior

✅ Phase 4: PDF Extraction Reliability
8. Dual-Mode PDF Text Extraction

Problem

Scanned PDFs returned no text

Fix

Primary: pdfplumber

Fallback: extract_text_robust() using OCR/pdfminer

Automatic fallback when extracted text is too short

This ensured maximum PDF compatibility.

✅ Phase 5: Bias Detection (OpenAI)
9. Replaced Gemini Bias Analyzer with OpenAI

Reasons

Gemini free-tier quota exhaustion (429 errors)

Demo reliability concerns

Fix

Introduced OpenAIBiasAnalyzer

Uses low-token, quota-safe OpenAI models

Analyzes Abstract + Conclusions only (efficient & meaningful)

10. Added Bias Availability Detection

Behavior

If OPENAI_API_KEY is missing:

Bias analysis safely disables

UI shows a clear explanation instead of failing

Log Example

INFO:api:Bias enabled: False

✅ Phase 6: Frontend Stability (Streamlit)
11. Fixed Page Disappearing on “Analyze”

Root Cause

Streamlit reruns removed UI elements due to conditional layout

Fix

Rewrote app.py so:

Layout is always rendered

Results appear inside a persistent container

Prevented UI from vanishing on button click

🟢 Current System State
✔ What Works Reliably Now

PDF upload (including scanned PDFs)

Section-wise plagiarism detection

Weighted overall similarity score

Semantic search with real academic sources

Bias detection (when API key present)

Stable frontend rendering

⚠️ Intentional Design Choices

Low plagiarism thresholds for demo visibility

Bias detection gracefully disabled if API key missing

No frontend refactor required

🚀 Recommended Next Enhancements

Sentence-level plagiarism highlighting

Cross-language plagiarism detection

Downloadable plagiarism/bias reports (PDF)

IEEE/OpenAlex source toggles

Demo vs Production mode switch

Maintained by:
Research Paper Plagiarism & Bias Detection Team
Last Updated: Auto-generated during stabilization phase