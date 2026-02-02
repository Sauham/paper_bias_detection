import fitz  # PyMuPDF
from pdfminer.high_level import extract_text as pdfminer_extract
from pdf2image import convert_from_path
import pytesseract
import os
import re


MIN_TEXT_LENGTH = 500  # heuristic


def _normalize_extracted_text(text: str) -> str:
    """
    Normalize extracted text to fix common PDF extraction issues.
    """
    if not text:
        return ""
    
    # 1. Replace various unicode spaces with regular space
    text = re.sub(r'[\u00A0\u2000-\u200B\u202F\u205F\u3000]', ' ', text)
    
    # 2. Fix ligatures and special characters
    ligatures = {
        'ﬁ': 'fi', 'ﬂ': 'fl', 'ﬀ': 'ff', 'ﬃ': 'ffi', 'ﬄ': 'ffl',
        '—': '-', '–': '-', ''': "'", ''': "'", '"': '"', '"': '"',
    }
    for lig, replacement in ligatures.items():
        text = text.replace(lig, replacement)
    
    # 3. Add spaces around punctuation that might be missing spaces
    text = re.sub(r'\.([A-Z])', r'. \1', text)  # Period followed by capital
    text = re.sub(r',([A-Za-z])', r', \1', text)  # Comma followed by letter
    
    # 4. Fix hyphenated line breaks (word- continuation on next line)
    text = re.sub(r'-\s*\n\s*', '', text)
    
    # 5. Normalize multiple spaces and newlines
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # 6. Add space between lowercase and uppercase (camelCase from PDF issues)
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    
    return text.strip()


def extract_with_pymupdf(pdf_path: str) -> str:
    text = []
    try:
        doc = fitz.open(pdf_path)
        for page in doc:
            # Use "dict" mode for better text extraction with spacing
            page_text = page.get_text("text", flags=fitz.TEXT_PRESERVE_WHITESPACE)
            text.append(page_text)
        doc.close()
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
    """
    Extract text from PDF using multiple methods with fallback.
    Returns normalized text with proper spacing.
    """
    # 1️⃣ PyMuPDF (fast, good for most PDFs)
    text = extract_with_pymupdf(pdf_path)
    if len(text.strip()) >= MIN_TEXT_LENGTH:
        return _normalize_extracted_text(text)

    # 2️⃣ pdfminer (better for complex layouts)
    text = extract_with_pdfminer(pdf_path)
    if len(text.strip()) >= MIN_TEXT_LENGTH:
        return _normalize_extracted_text(text)

    # 3️⃣ OCR (scanned PDFs)
    text = extract_with_ocr(pdf_path)
    return _normalize_extracted_text(text)
