from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pdfplumber
import io
import logging
import tempfile
import os
from dotenv import load_dotenv

from src.bias_analyzer import BiasAnalyzer, result_to_dict
from src.plagiarism_checker import analyze_plagiarism, extract_sections
from src.text_extraction import extract_text_robust

# -------------------------------------------------
# Setup
# -------------------------------------------------

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bias_analyzer = BiasAnalyzer()
ai_provider = os.getenv("AI_PROVIDER", "gemini")
logger.info(f"Bias analysis enabled: {bias_analyzer.enabled}, Primary provider: {ai_provider}")

app = FastAPI(title="Paper Similarity & Bias Detection API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------
# ORIGINAL extraction function (frontend-compatible)
# -------------------------------------------------

def extract_pdf_text_from_bytes(data: bytes) -> str:
    text = ""
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            if page_text:
                text += page_text + "\n"
    return text


# -------------------------------------------------
# API
# -------------------------------------------------

@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    try:
        data = await file.read()

        # 1️⃣ Original extraction (what frontend expects)
        full_text = extract_pdf_text_from_bytes(data)

        # 2️⃣ Robust fallback (safe, invisible to frontend)
        if len(full_text.strip()) < 300:
            logger.info("Weak text from pdfplumber, using robust extractor")
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(data)
                tmp_path = tmp.name
            try:
                full_text = extract_text_robust(tmp_path)
            finally:
                os.remove(tmp_path)

        if not full_text.strip():
            return JSONResponse(
                status_code=400,
                content={"error": "No text extracted from PDF"}
            )

        # 3️⃣ Plagiarism analysis
        plagiarism_report = analyze_plagiarism(full_text)

        # 4️⃣ Bias analysis (Gemini)
        sections = extract_sections(full_text)
        bias_result = bias_analyzer.analyze_paper_sections(sections)
        bias_dict = result_to_dict(bias_result)

        # Return response
        return {
            "plagiarism": {
                "overall_percent": plagiarism_report.get("overall_percent", 0),
                "overall_category": plagiarism_report.get("overall_category", ""),
                "sections": plagiarism_report.get("sections", {})
            },
            "bias_analysis": bias_dict
        }


    except Exception as e:
        logger.exception("Analysis error")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.get("/")
async def root():
    return {
        "message": "Paper Bias Detection API",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "analyze": "/analyze (POST with PDF file)"
        },
        "bias_analysis_enabled": bias_analyzer.enabled
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
