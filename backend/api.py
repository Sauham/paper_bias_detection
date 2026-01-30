from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pdfplumber
import io
import logging
import tempfile
import os
from dotenv import load_dotenv

from src.openai_bias_analyzer import OpenAIBiasAnalyzer
from src.plagiarism_checker import analyze_plagiarism, extract_sections
from src.text_extraction import extract_text_robust

# -------------------------------------------------
# Setup
# -------------------------------------------------

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bias_analyzer = OpenAIBiasAnalyzer()
logger.info(f"Bias enabled: {bias_analyzer.enabled}")

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

        # 4️⃣ Bias analysis (OpenAI)
        bias_result = bias_analyzer.analyze_sections(
            extract_sections(full_text)
        )



        # 🔴 EXACT OLD RESPONSE SHAPE (DO NOT CHANGE)
        return {
            "plagiarism": {
                "overall_percent": plagiarism_report.get("overall_percent", 0),
                "overall_category": plagiarism_report.get("overall_category", ""),
                "sections": plagiarism_report.get("sections", {})
            },
            "bias_analysis": bias_result
        }


    except Exception as e:
        logger.exception("Analysis error")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.get("/health")
async def health():
    return {"status": "ok"}
