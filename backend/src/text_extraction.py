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


def _count_valid_words(text: str) -> int:
    """Count words that look like valid English words (not truncated)."""
    words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
    # Common word patterns - valid words usually start with common letter combinations
    valid_starts = {'th', 'an', 'in', 're', 'on', 'at', 'en', 'er', 'ou', 'it', 'es', 'st', 
                   'or', 'te', 'of', 'ed', 'is', 'ar', 'al', 'to', 'co', 'de', 'ra', 'ri',
                   'ro', 'be', 'wa', 'ha', 'wi', 'as', 'fo', 'pr', 'no', 'se', 'so', 'un',
                   'us', 'ab', 'ac', 'ad', 'af', 'ag', 'ai', 'am', 'ap', 'au', 'av', 'ba',
                   'bi', 'bl', 'bo', 'br', 'bu', 'ca', 'ce', 'ch', 'ci', 'cl', 'cr', 'cu',
                   'da', 'di', 'do', 'dr', 'du', 'ea', 'ec', 'ef', 'el', 'em', 'ev', 'ex',
                   'fa', 'fe', 'fi', 'fl', 'fr', 'fu', 'ga', 'ge', 'gi', 'gl', 'go', 'gr',
                   'gu', 'he', 'hi', 'ho', 'hu', 'id', 'ig', 'im', 'io', 'ir', 'ja', 'jo',
                   'ju', 'ke', 'ki', 'kn', 'la', 'le', 'li', 'lo', 'lu', 'ma', 'me', 'mi',
                   'mo', 'mu', 'na', 'ne', 'ni', 'nu', 'ob', 'oc', 'of', 'op', 'ot', 'ov',
                   'pa', 'pe', 'ph', 'pi', 'pl', 'po', 'qu', 'ra', 'sc', 'sh', 'si', 'sk',
                   'sl', 'sm', 'sn', 'sp', 'sq', 'su', 'sw', 'sy', 'ta', 'tr', 'tw', 'ty',
                   'va', 've', 'vi', 'vo', 'we', 'wh', 'wo', 'wr', 'ye', 'yo'}
    
    valid_count = 0
    for word in words:
        if len(word) >= 2 and word[:2] in valid_starts:
            valid_count += 1
    
    return valid_count


def extract_with_pymupdf(pdf_path: str) -> str:
    """Extract using PyMuPDF with multiple strategies."""
    best_text = ""
    best_valid_words = 0
    
    try:
        doc = fitz.open(pdf_path)
        
        # Strategy 1: Default text extraction
        text1 = []
        for page in doc:
            text1.append(page.get_text("text"))
        text1 = "\n".join(text1)
        valid1 = _count_valid_words(text1)
        if valid1 > best_valid_words:
            best_text = text1
            best_valid_words = valid1
        
        # Strategy 2: With whitespace preservation
        text2 = []
        for page in doc:
            text2.append(page.get_text("text", flags=fitz.TEXT_PRESERVE_WHITESPACE))
        text2 = "\n".join(text2)
        valid2 = _count_valid_words(text2)
        if valid2 > best_valid_words:
            best_text = text2
            best_valid_words = valid2
        
        # Strategy 3: Using blocks for better structure
        text3 = []
        for page in doc:
            blocks = page.get_text("blocks")
            for block in blocks:
                if block[6] == 0:  # Text block (not image)
                    text3.append(block[4])
        text3 = "\n".join(text3)
        valid3 = _count_valid_words(text3)
        if valid3 > best_valid_words:
            best_text = text3
            best_valid_words = valid3
        
        # Strategy 4: Raw text with sorting
        text4 = []
        for page in doc:
            text4.append(page.get_text("text", sort=True))
        text4 = "\n".join(text4)
        valid4 = _count_valid_words(text4)
        if valid4 > best_valid_words:
            best_text = text4
            best_valid_words = valid4
        
        doc.close()
        logger.debug(f"PyMuPDF best strategy had {best_valid_words} valid words")
        
    except Exception as e:
        logger.warning(f"PyMuPDF extraction error: {e}")
    
    return best_text


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
