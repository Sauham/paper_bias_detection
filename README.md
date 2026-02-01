# Research Paper Analyzer

A comprehensive web tool for analyzing academic papers for plagiarism and bias detection.

## Project Overview

Research Paper Analyzer is an AI-powered tool that reads academic papers (PDF), extracts main sections — Title, Abstract, Methodology, and Conclusions — and provides:

1. **Plagiarism Detection**: Evaluates similarity against published academic work
2. **AI Bias Analysis**: Detects various types of academic bias using Google's Gemini AI

## Features

### Plagiarism Detection
- Extracts text from uploaded PDFs (with robust fallbacks using PyMuPDF, pdfminer, and OCR)
- Splits content into four sections: Title, Abstract, Methodology, Conclusions
- Searches multiple academic databases:
  - **IEEE Xplore** (requires API key)
  - **Semantic Scholar**
  - **OpenAlex**
- Computes TF-IDF cosine similarity to estimate overlap
- Classifies similarity levels:
  - 0–25%: Low similarity (mostly original)
  - 25–50%: Moderate similarity
  - >50%: High similarity (review recommended)
- Displays top matching sources with direct links

### AI Bias Analysis
Powered by Google's Gemini AI, detects:
- **Confirmation Bias**: Language assuming conclusions before evidence
- **Selection Bias**: Non-representative sampling indicators
- **Publication Bias**: Overly positive framing, suppressed negative results
- **Funding Bias**: Undisclosed conflicts of interest
- **Citation Bias**: Selective citing supporting predetermined views
- **Methodology Bias**: Flawed experimental design

Provides:
- Overall bias score (0-100)
- Detailed explanations for each detected bias
- Actionable suggestions for improvement
- Identified strengths in the paper

## Tech Stack

### Backend
- Python 3.9+
- FastAPI
- Google Generative AI (Gemini)
- PDF Processing: PyMuPDF, pdfplumber, pdfminer.six, pytesseract
- ML: scikit-learn, numpy, scipy

### Frontend
- React 18 (Vite)
- TypeScript
- Axios
- Modern dark theme UI

---

## Repository Layout

```
backend/
  api.py                     # FastAPI server, POST /analyze endpoint
  requirements.txt           # Python dependencies
  .env                       # Environment variables (API keys)
  .env.example               # Environment template
  src/
    gemini_bias_analyzer.py  # Gemini AI bias detection
    plagiarism_checker.py    # Section extraction, similarity analysis
    text_extraction.py       # PDF text extraction (multi-method)
    integrations/
      ieee_explore.py        # IEEE Xplore API integration

web/
  index.html                 # HTML entry point
  src/
    main.tsx                 # React entry
    ui/
      App.tsx                # Main application UI
      BiasAnalysisSection.tsx # Bias analysis results component
  vite.config.ts             # Vite configuration
```

---

## Requirements

### Backend
- Python 3.9+
- Gemini API key (for bias analysis)
- IEEE Xplore API key (optional, for enhanced plagiarism detection)

### Frontend
- Node.js 18+
- npm, pnpm, or yarn

---

## Setup & Run

### 1. Clone the Repository

```bash
git clone https://github.com/rk0802p/paper_bias_detection.git
cd paper_bias_detection
```

### 2. Configure Environment Variables

Copy the example environment file and add your API keys:

```bash
cd backend
cp .env.example .env
```

Edit `.env` with your keys:

```env
# Required for bias analysis
GEMINI_API_KEY=your_gemini_api_key_here

# Model selection - choose one:
#   gemini-2.5-flash  (recommended - latest and fastest)
#   gemini-2.0-flash  (stable)
#   gemini-1.5-flash  (legacy)
#   gemini-1.5-pro    (slower but more capable)
GEMINI_MODEL=gemini-2.0-flash

BIAS_ANALYSIS_ENABLED=true

# Optional - enhances plagiarism detection with IEEE papers
IEEE_API_KEY=your_ieee_api_key_here
```

### Switching Gemini Models

To use a different Gemini model, simply change the `GEMINI_MODEL` value in your `.env` file:

```env
# For the latest Gemini 2.5 Flash (recommended):
GEMINI_MODEL=gemini-2.5-flash

# For Gemini 2.0 Flash:
GEMINI_MODEL=gemini-2.0-flash

# For Gemini 1.5 Pro (more capable, slower):
GEMINI_MODEL=gemini-1.5-pro
```

**Get API Keys:**
- Gemini API: https://aistudio.google.com/app/apikey
- IEEE Xplore API: https://developer.ieee.org/

### 3. Start the Backend

```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate (macOS/Linux)
source .venv/bin/activate
# Activate (Windows)
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start server
uvicorn api:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

### 4. Start the Frontend

```bash
cd web
npm install
npm run dev
```

Open `http://localhost:5173` in your browser.

---

## API Endpoints

### POST /analyze
Upload a PDF file for analysis.

**Request:**
- Content-Type: `multipart/form-data`
- Body: `file` (PDF file)

**Response:**
```json
{
  "plagiarism": {
    "overall_percent": 14.9,
    "overall_category": "Low similarity",
    "sections": {
      "Title": { "best_similarity_percent": 0, "matches": [] },
      "Abstract": { "best_similarity_percent": 32.9, "matches": [...] },
      "Methodology": { "best_similarity_percent": 0, "matches": [] },
      "Conclusions": { "best_similarity_percent": 2.0, "matches": [...] }
    }
  },
  "bias_analysis": {
    "overall_score": 25,
    "severity": "low",
    "summary": "...",
    "biases": [...],
    "strengths": [...]
  }
}
```

### GET /health
Health check endpoint.

---

## Troubleshooting

### Bias Analysis Shows "Unavailable"

**Rate Limit Error**: The Gemini API free tier has daily limits. Either:
- Wait for quota reset (resets daily)
- Upgrade to paid plan at [Google AI Studio](https://aistudio.google.com/)
- Use a different API key

**API Key Error**: Ensure `GEMINI_API_KEY` is correctly set in `.env`

### Port Already in Use

```bash
# Kill process on port 8000
kill -9 $(lsof -t -i:8000)

# Or use a different port
uvicorn api:app --reload --port 8001
```

### No IEEE Results

- Verify `IEEE_API_KEY` is set in `.env`
- IEEE search may not find matches for all topics
- Semantic Scholar and OpenAlex provide fallback results

---

## Notes & Limitations

- Similarity scores are approximate signals for manual review, not legal plagiarism determinations
- Bias analysis quality depends on Gemini AI availability and quota
- Retrieval quality depends on public API availability
- For scanned/image PDFs, OCR support is available but requires tesseract installed

---

## License

MIT License
