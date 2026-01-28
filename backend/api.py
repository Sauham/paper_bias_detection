from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pdfplumber
import io
import os
import logging
from dotenv import load_dotenv

from src.plagiarism_checker import analyze_plagiarism, extract_sections
from src.gemini_bias_analyzer import GeminiBiasAnalyzer, result_to_dict

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Paper Similarity & Bias Detection API")

app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

# Initialize Gemini Bias Analyzer
bias_analyzer = GeminiBiasAnalyzer()
logger.info(f"Bias analyzer enabled: {bias_analyzer.enabled}")


def extract_pdf_text_from_bytes(data: bytes) -> str:
	text = ""
	with pdfplumber.open(io.BytesIO(data)) as pdf:
		for page in pdf.pages:
			page_text = page.extract_text() or ""
			if len(page_text.strip()) < 80:
				try:
					words = page.extract_words()
					if words:
						page_text = " ".join(w.get("text", "") for w in words)
				except Exception:
					pass
			if page_text:
				text += page_text + "\n"
	return text


@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
	try:
		data = await file.read()
		full_text = extract_pdf_text_from_bytes(data)
		if not full_text.strip():
			return JSONResponse(status_code=400, content={"error": "No text extracted from PDF"})
		
		# Run plagiarism analysis
		plagiarism_report = analyze_plagiarism(full_text)
		
		# Run bias analysis using Gemini
		sections = extract_sections(full_text)
		bias_result = bias_analyzer.analyze_paper_sections(sections)
		bias_report = result_to_dict(bias_result)
		
		# Combine reports
		combined_report = {
			"plagiarism": {
				"overall_percent": plagiarism_report.get("overall_percent", 0),
				"overall_category": plagiarism_report.get("overall_category", ""),
				"sections": plagiarism_report.get("sections", {})
			},
			"bias_analysis": bias_report
		}
		
		return combined_report
	except Exception as e:
		logger.error(f"Analysis error: {e}")
		return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/health")
async def health():
	return {
		"status": "ok",
		"bias_analysis_enabled": bias_analyzer.enabled
	}

