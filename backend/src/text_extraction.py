import fitz  # PyMuPDF
from pdfminer.high_level import extract_text as pdfminer_extract
from pdf2image import convert_from_path
import pytesseract
import os


MIN_TEXT_LENGTH = 500  # heuristic


def extract_with_pymupdf(pdf_path: str) -> str:
    text = []
    try:
        doc = fitz.open(pdf_path)
        for page in doc:
            text.append(page.get_text("text"))
    except Exception:
        pass
    return "\n".join(text)


def extract_with_pdfminer(pdf_path: str) -> str:
    try:
        return pdfminer_extract(pdf_path)
    except Exception:
        return ""


def extract_with_ocr(pdf_path: str) -> str:
    text = []
    try:
        images = convert_from_path(pdf_path, dpi=300)
        for img in images:
            text.append(pytesseract.image_to_string(img))
    except Exception:
        pass
    return "\n".join(text)


def extract_text_robust(pdf_path: str) -> str:
    # 1️⃣ PyMuPDF
    text = extract_with_pymupdf(pdf_path)
    if len(text.strip()) >= MIN_TEXT_LENGTH:
        return text

    # 2️⃣ pdfminer
    text = extract_with_pdfminer(pdf_path)
    if len(text.strip()) >= MIN_TEXT_LENGTH:
        return text

    # 3️⃣ OCR (scanned PDFs)
    text = extract_with_ocr(pdf_path)
    return text
