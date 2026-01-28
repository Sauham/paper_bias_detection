# Research Paper Plagiarism & Bias Detection System - Architecture Document

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [System Architecture](#2-system-architecture)
3. [Technology Stack](#3-technology-stack)
4. [Backend Architecture](#4-backend-architecture)
5. [Frontend Architecture](#5-frontend-architecture)
6. [Core Algorithms & Concepts](#6-core-algorithms--concepts)
7. [Data Flow](#7-data-flow)
8. [API Reference](#8-api-reference)
9. [Directory Structure](#9-directory-structure)
10. [Testing Strategy](#10-testing-strategy)

---

## 1. Project Overview

This project is a **Research Paper Plagiarism and Bias Detection System** designed to analyze academic papers for:
- **Similarity/Plagiarism Detection**: Compares uploaded papers against scholarly databases to identify potential plagiarism
- **Bias Detection**: Identifies various types of biases in academic writing (confirmation bias, selection bias, publication bias)
- **Quality Assessment**: Evaluates methodology strength, data/code availability, and sample size adequacy
- **Citation Analysis**: Builds citation networks and calculates impact metrics using graph algorithms

The system provides a web-based interface where users can upload PDF documents and receive comprehensive analysis reports.

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           CLIENT LAYER                                   │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    React Web Application                         │    │
│  │    • PDF Upload Interface                                        │    │
│  │    • Results Visualization (Sections, Matches, Scores)           │    │
│  │    • Responsive UI with Expandable Sections                      │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────┬──────────────────────────────────────┘
                                   │ HTTP/REST (JSON)
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           API LAYER                                      │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                     FastAPI Server                               │    │
│  │    • POST /analyze - PDF Analysis Endpoint                       │    │
│  │    • GET /health - Health Check                                  │    │
│  │    • CORS Middleware                                             │    │
│  │    • PDF Text Extraction (pdfplumber)                            │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────┬──────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        PROCESSING LAYER                                  │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐                │
│  │  Plagiarism   │  │    Bias       │  │   Quality     │                │
│  │   Checker     │  │   Analyzer    │  │   Assessor    │                │
│  └───────────────┘  └───────────────┘  └───────────────┘                │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐                │
│  │   Citation    │  │    Text       │  │  Traditional  │                │
│  │   Analyzer    │  │ Preprocessor  │  │    Models     │                │
│  └───────────────┘  └───────────────┘  └───────────────┘                │
└──────────────────────────────────┬──────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       EXTERNAL SERVICES                                  │
│  ┌───────────────────────┐  ┌───────────────────────┐                   │
│  │   Semantic Scholar    │  │      OpenAlex         │                   │
│  │        API            │  │        API            │                   │
│  └───────────────────────┘  └───────────────────────┘                   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Technology Stack

### Backend
| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.8+ | Primary backend language |
| **FastAPI** | Latest | REST API framework with async support |
| **Uvicorn** | Latest | ASGI server for FastAPI |
| **pdfplumber** | Latest | PDF text extraction |
| **scikit-learn** | Latest | TF-IDF vectorization, ML models |
| **NumPy** | Latest | Numerical computations |
| **SciPy** | Latest | Scientific computing |
| **spaCy** | Latest | NLP preprocessing (en_core_web_sm) |
| **Transformers** | Latest | DistilBERT for bias detection |
| **PyTorch** | Latest | Deep learning framework |
| **NetworkX** | Latest | Citation graph analysis |
| **Pandas** | Latest | Data manipulation |
| **Requests** | Latest | External API calls |
| **BeautifulSoup** | Latest | Web scraping (data collection) |

### Frontend
| Technology | Version | Purpose |
|------------|---------|---------|
| **React** | 18.2.0 | UI framework |
| **TypeScript/TSX** | Latest | Type-safe JavaScript |
| **Vite** | 5.3.0 | Build tool & dev server |
| **Axios** | 1.7.2 | HTTP client for API calls |

### External APIs
| Service | Purpose |
|---------|---------|
| **Semantic Scholar API** | Academic paper search & metadata |
| **OpenAlex API** | Open scholarly data repository |

---

## 4. Backend Architecture

### 4.1 API Layer (`backend/api.py`)

The FastAPI application serves as the entry point:

```python
# Key Components:
- FastAPI app with CORS middleware (allows all origins)
- PDF text extraction using pdfplumber
- Async endpoint for file upload processing
```

**Endpoints:**
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/analyze` | Upload PDF for plagiarism analysis |
| `GET` | `/health` | Server health check |

### 4.2 Core Modules

#### 4.2.1 Plagiarism Checker (`src/plagiarism_checker.py`)

**Primary module for similarity detection.**

**Key Functions:**
- `extract_sections(full_text)` - Parses PDF text into sections (Title, Abstract, Methodology, Conclusions) using regex-based heuristics
- `search_related_papers(query_text)` - Queries Semantic Scholar and OpenAlex APIs for similar papers
- `similarity_percent(a, b)` - Calculates TF-IDF cosine similarity between two texts
- `analyze_section(section_text)` - Analyzes individual sections for plagiarism
- `analyze_plagiarism(full_text)` - Main orchestrator returning complete report

**Section Extraction Logic:**
```
1. Title: First non-empty line (≤200 chars)
2. Abstract: Detected by heading pattern "abstract"
3. Methodology: Patterns include "methodology", "methods", "experimental setup"
4. Conclusions: Patterns include "conclusion", "summary", "discussion"
5. Fallbacks: If markers not found, uses paragraph positions
```

**Similarity Categorization:**
| Range | Category |
|-------|----------|
| 1-25% | Low similarity (mostly original ideas) |
| 25-50% | Moderate similarity |
| >50% | High similarity (heavily copied) |

**Weighted Overall Score:**
| Section | Weight |
|---------|--------|
| Title | 10% |
| Abstract | 40% |
| Methodology | 40% |
| Conclusions | 10% |

#### 4.2.2 Advanced Bias Analyzer (`src/advanced_bias_analyzer.py`)

**Linguistic pattern-based bias detection.**

**Bias Types Detected:**

1. **Confirmation Bias** - Language indicating predetermined conclusions
   - Patterns: "confirms our hypothesis", "proves our theory", "as we predicted", "clearly shows", "obviously superior"

2. **Selection Bias** - Indicators of non-representative sampling
   - Patterns: "participants were excluded", "sample was limited to", "convenience sample", "we consider only"

3. **Publication Bias** - Language suggesting results-driven publishing
   - Patterns: "state-of-the-art", "outperforms", "breakthrough", "novel approach", "superior performance"

**Statistical Analyzer Class:**
- `extract_p_values(text)` - Extracts p-values using regex: `p\s*(?:<|=|>)\s*(\d*\.?\d+)`
- `detect_p_hacking(p_values)` - Flags suspicious clustering of p-values near 0.05
- `validate_methodology(text)` - Checks for control groups, randomization, blinding

#### 4.2.3 Bias Detector Model (`src/bias_detector_model.py`)

**Deep learning-based bias classification using DistilBERT.**

**Architecture:**
```
Input Text → DistilBERT Tokenizer → DistilBERT Encoder → Classification Head → Bias Labels
```

**Model Configuration:**
- Base Model: `distilbert-base-uncased`
- Task: Multi-class classification (5 bias types)
- Training: HuggingFace Trainer API
- Batch Size: 16 (train), 64 (eval)
- Epochs: 3
- Warmup Steps: 500
- Weight Decay: 0.01

#### 4.2.4 Text Preprocessor (`src/text_preprocessor.py`)

**NLP preprocessing pipeline using spaCy and Transformers.**

**Capabilities:**
- Sentence segmentation using spaCy's `en_core_web_sm` model
- Citation extraction via regex: `\[(\d+(?:,\s*\d+)*)\]`
- Integration with DistilBERT tokenizer for ML pipeline

#### 4.2.5 Citation Analyzer (`src/citation_analyzer.py`)

**Graph-based citation network analysis using NetworkX.**

**Features:**
- Builds directed citation graph (DiGraph)
- Calculates **PageRank** - measures paper influence
- Calculates **Betweenness Centrality** - identifies papers that bridge different research areas

**Graph Structure:**
```
Nodes: Papers (with metadata: title, year)
Edges: Citation relationships (directed from citing to cited)
```

#### 4.2.6 Quality Assessor (`src/quality_assessor.py`)

**Multi-dimensional quality assessment framework.**

**Quality Metrics:**
| Metric | Weight | Detection Method |
|--------|--------|------------------|
| Data Availability | 20% | Pattern matching for data statements |
| Code Availability | 20% | GitHub/GitLab links, "code available" |
| Methodology Strength | 40% | Control groups, randomization, blinding |
| Sample Size | 20% | Log-scaled scoring of reported n |

**Unified Quality Score:**
```python
score = Σ(metric_score × weight)  # Range: 0.0 - 1.0
```

**Confidence Intervals:**
Simple ±0.1 interval around computed score (placeholder for statistical CI).

#### 4.2.7 Traditional Models (`src/traditional_models.py`)

**Classical ML approaches for bias detection.**

**Components:**

1. **TF-IDF + Logistic Regression**
   - Feature extraction: TF-IDF with 5000 max features
   - Binary classification: Bias vs No Bias
   - Train/test split: 70/30

2. **Rule-Based Detector**
   - Keyword matching for funding bias
   - Patterns: "funded by", "sponsored by", "financial support from"

3. **Ensemble Model (Placeholder)**
   - Combines DL, TF-IDF, and rule-based predictions
   - Majority voting scheme

#### 4.2.8 Data Collector (`src/data_collector.py`)

**Academic paper collection and preprocessing pipeline.**

**Data Sources (Placeholder implementations):**
- arXiv
- PubMed
- ACL Anthology

**Pipeline:**
```
Fetch Paper → Extract PDF Text → Preprocess → Save Sentences
```

#### 4.2.9 Annotation Tool (`src/annotation_tool.py`)

**Interactive CLI tool for creating training datasets.**

**Bias Labels:**
| Index | Label |
|-------|-------|
| 0 | Selection Bias |
| 1 | Funding Bias |
| 2 | Publication Bias |
| 3 | Cognitive Bias |
| 4 | No Bias |

**Output Format:** CSV with columns `[sentence, bias_type, label]`

#### 4.2.10 Dataset Utilities (`src/dataset_utils.py`)

**Dataset balancing and augmentation.**

**Balancing Strategy:**
- Undersampling: Reduces majority class to match minority class size
- Preserves class ratio for fair training

**Data Augmentation (Placeholder):**
- Back-translation
- Synonym replacement

#### 4.2.11 Validation (`src/validation.py`)

**Dataset quality assurance tools.**

**Features:**
- **Inter-Annotator Agreement (IAA)**: Cohen's Kappa score between annotators
- **Quality Checks**: Missing labels, label consistency validation

---

## 5. Frontend Architecture

### 5.1 Application Structure

```
web/
├── index.html          # Entry HTML with CSS variables
├── vite.config.ts      # Build configuration with API proxy
├── package.json        # Dependencies
└── src/
    ├── main.tsx        # React root mount
    └── ui/
        └── App.tsx     # Main application component
```

### 5.2 UI Components

#### Main App Component (`App.tsx`)

**State Management:**
```typescript
const [file, setFile] = useState<File|null>(null)      // Selected PDF
const [loading, setLoading] = useState(false)           // Loading state
const [error, setError] = useState<string|null>(null)   // Error messages
const [report, setReport] = useState<any>(null)         // Analysis results
```

**Features:**
- PDF file upload with drag-and-drop support
- Async API call to backend `/analyze` endpoint
- Collapsible section components for results display
- Error handling and loading states

#### Section Component

Displays per-section analysis with:
- Best similarity percentage
- Category classification
- Expandable match table (title, percentage, link)

### 5.3 Styling

**Design System (CSS Variables):**
```css
:root {
  --bg: #f1eee7;      /* Parchment background */
  --panel: #e5e1d5;    /* Panel background */
  --ink: #2b2119;      /* Dark brown text */
  --accent: #a64b2a;   /* Burgundy-orange accent */
}
```

**Visual Theme:** Academic/scholarly aesthetic with serif fonts and parchment-like textures.

### 5.4 Build Configuration (`vite.config.ts`)

```typescript
- Dev server port: 5173
- API proxy: /analyze → localhost:8000
- API proxy: /health → localhost:8000
```

---

## 6. Core Algorithms & Concepts

### 6.1 TF-IDF (Term Frequency-Inverse Document Frequency)

**Purpose:** Convert text to numerical vectors for similarity comparison.

**Formula:**
$$TF\text{-}IDF(t,d) = TF(t,d) \times IDF(t)$$

Where:
- $TF(t,d)$ = Frequency of term $t$ in document $d$
- $IDF(t) = \log\frac{N}{df(t)}$ where $N$ = total documents, $df(t)$ = documents containing $t$

**Implementation:** `sklearn.feature_extraction.text.TfidfVectorizer` with English stop words removed.

### 6.2 Cosine Similarity

**Purpose:** Measure similarity between two document vectors.

**Formula:**
$$\text{cosine}(\vec{A}, \vec{B}) = \frac{\vec{A} \cdot \vec{B}}{||\vec{A}|| \times ||\vec{B}||}$$

**Range:** 0 (completely different) to 1 (identical)

**Implementation:** `sklearn.metrics.pairwise.cosine_similarity`

### 6.3 PageRank Algorithm

**Purpose:** Rank papers by influence in citation network.

**Concept:** A paper is important if it's cited by other important papers.

**Formula:**
$$PR(p) = \frac{1-d}{N} + d \sum_{q \in M(p)} \frac{PR(q)}{L(q)}$$

Where:
- $d$ = damping factor (typically 0.85)
- $M(p)$ = set of papers citing $p$
- $L(q)$ = number of outbound citations from $q$

**Implementation:** `networkx.pagerank()`

### 6.4 Betweenness Centrality

**Purpose:** Identify papers that connect different research clusters.

**Formula:**
$$BC(v) = \sum_{s \neq v \neq t} \frac{\sigma_{st}(v)}{\sigma_{st}}$$

Where $\sigma_{st}$ = number of shortest paths from $s$ to $t$, and $\sigma_{st}(v)$ = paths through $v$.

**Implementation:** `networkx.betweenness_centrality()`

### 6.5 Cohen's Kappa

**Purpose:** Measure inter-annotator agreement accounting for chance.

**Formula:**
$$\kappa = \frac{p_o - p_e}{1 - p_e}$$

Where:
- $p_o$ = observed agreement
- $p_e$ = expected agreement by chance

**Interpretation:**
| κ Value | Agreement Level |
|---------|-----------------|
| < 0 | Less than chance |
| 0.01-0.20 | Slight |
| 0.21-0.40 | Fair |
| 0.41-0.60 | Moderate |
| 0.61-0.80 | Substantial |
| 0.81-1.00 | Almost perfect |

### 6.6 DistilBERT Architecture

**Purpose:** Transformer-based text classification for bias detection.

**Key Features:**
- 6-layer transformer (vs BERT's 12 layers)
- 40% smaller, 60% faster than BERT
- Retains 97% of BERT's language understanding

**Classification Head:** Linear layer mapping 768-dim embeddings to num_labels classes.

### 6.7 P-Hacking Detection Heuristic

**Purpose:** Identify potential statistical manipulation.

**Logic:**
```python
suspicious = [p for p in p_values if 0.04 < p < 0.05]
if len(suspicious) / len(p_values) > 0.5:
    return True  # P-hacking suspected
```

**Rationale:** Legitimate research shouldn't cluster p-values just below significance threshold.

---

## 7. Data Flow

### 7.1 Plagiarism Analysis Flow

```
┌──────────┐    ┌─────────────┐    ┌────────────────┐    ┌─────────────┐
│  PDF     │───▶│  Extract    │───▶│   Section      │───▶│  API Query  │
│  Upload  │    │  Text       │    │   Parsing      │    │  (SS/OA)    │
└──────────┘    └─────────────┘    └────────────────┘    └─────────────┘
                                                                │
┌──────────┐    ┌─────────────┐    ┌────────────────┐          │
│  Report  │◀───│  Aggregate  │◀───│   TF-IDF       │◀─────────┘
│  JSON    │    │  Scores     │    │   Similarity   │
└──────────┘    └─────────────┘    └────────────────┘
```

### 7.2 Request/Response Format

**Request:**
```
POST /analyze
Content-Type: multipart/form-data
Body: file=<PDF binary>
```

**Response:**
```json
{
  "overall_percent": 35.42,
  "overall_category": "25–50%: Moderate similarity",
  "sections": {
    "Title": {
      "best_similarity_percent": 12.5,
      "category": "1–25%: Low similarity",
      "matches": [
        {
          "percent": 12.5,
          "title": "Similar Paper Title",
          "url": "https://semanticscholar.org/..."
        }
      ]
    },
    "Abstract": { ... },
    "Methodology": { ... },
    "Conclusions": { ... }
  }
}
```

---

## 8. API Reference

### POST /analyze

Upload a PDF for plagiarism analysis.

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| file | File | Body (multipart) | Yes | PDF document to analyze |

**Responses:**

| Code | Description | Body |
|------|-------------|------|
| 200 | Success | Analysis report JSON |
| 400 | No text extracted | `{"error": "No text extracted from PDF"}` |
| 500 | Server error | `{"error": "<message>"}` |

### GET /health

Health check endpoint.

**Response:**
```json
{"status": "ok"}
```

---

## 9. Directory Structure

```
paper_bias_detection-main/
│
├── architecture.md              # This document
├── README.md                    # Project overview
│
├── backend/                     # Python backend
│   ├── __init__.py
│   ├── api.py                   # FastAPI application
│   ├── requirements.txt         # Python dependencies
│   └── src/
│       ├── plagiarism_checker.py     # Core similarity analysis
│       ├── advanced_bias_analyzer.py # Pattern-based bias detection
│       ├── bias_detector_model.py    # DistilBERT classifier
│       ├── text_preprocessor.py      # NLP preprocessing
│       ├── citation_analyzer.py      # NetworkX graph analysis
│       ├── quality_assessor.py       # Quality metrics
│       ├── traditional_models.py     # TF-IDF + Logistic Regression
│       ├── data_collector.py         # Paper collection pipeline
│       ├── annotation_tool.py        # Dataset annotation CLI
│       ├── dataset_utils.py          # Balancing & augmentation
│       └── validation.py             # IAA & quality checks
│
├── web/                         # React frontend
│   ├── index.html               # Entry HTML
│   ├── package.json             # NPM dependencies
│   ├── vite.config.ts           # Vite configuration
│   └── src/
│       ├── main.tsx             # React entry point
│       └── ui/
│           └── App.tsx          # Main application
│
└── tests/                       # Test suite
    └── test_quality_assessor.py # Quality assessor unit tests
```

---

## 10. Testing Strategy

### 10.1 Unit Tests

Located in `tests/` directory using Python's `unittest` framework.

**Current Coverage:**
- `test_quality_assessor.py` - Tests for quality assessment functions

**Test Categories:**
```python
- test_data_availability()    # Pattern matching validation
- test_unified_score()        # Score calculation accuracy
```

### 10.2 Running Tests

```bash
# From project root
cd backend
python -m pytest tests/ -v

# Or using unittest
python -m unittest discover tests/
```

### 10.3 Test Design Principles

- **Isolation:** Each test creates fresh instances
- **Assertions:** Clear expected vs actual comparisons
- **Coverage:** High and low quality text samples tested

---

## Appendix A: Environment Setup

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
python -m spacy download en_core_web_sm
uvicorn api:app --reload --port 8000
```

### Frontend Setup
```bash
cd web
npm install
npm run dev  # Starts on http://localhost:5173
```

### Environment Variables
```
# web/.env
VITE_API_BASE=http://localhost:8000
```

---

## Appendix B: External API Details

### Semantic Scholar API
- **Endpoint:** `https://api.semanticscholar.org/graph/v1/paper/search`
- **Rate Limit:** 100 requests/5 minutes (anonymous)
- **Fields Used:** title, url, abstract

### OpenAlex API
- **Endpoint:** `https://api.openalex.org/works`
- **Rate Limit:** 100,000 requests/day (polite pool)
- **Fields Used:** title, id, abstract_inverted_index

---

## Appendix C: Future Enhancements

1. **Trained Bias Detection Model** - Deploy fine-tuned DistilBERT
2. **Real-time Citation Graph** - Live visualization of paper networks
3. **Multi-language Support** - Extend beyond English papers
4. **Batch Processing** - Analyze multiple PDFs simultaneously
5. **User Authentication** - Save analysis history
6. **PDF Annotation** - Highlight detected issues in original document
7. **API Rate Limiting** - Handle external API quotas gracefully
8. **Confidence Scoring** - Statistical confidence intervals for all metrics
