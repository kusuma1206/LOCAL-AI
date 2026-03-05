import os
import re
from pathlib import Path
import fitz  # PyMuPDF
from docx import Document

def _normalize_text(text):
    """Normalize whitespace and line breaks while preserving paragraph boundaries."""
    if not text:
        return ""
    # Replace multiple spaces with single space
    text = re.sub(r'[ \t]+', ' ', text)
    # Replace 3 or more newlines with double newline (paragraph boundary)
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Strip leading/trailing whitespace
    return text.strip()

def _calculate_confidence(text, original_size_bytes):
    """
    Heuristic to estimate extraction confidence using a smoother exponential saturation curve.
    Formula: 1 - exp(-(k1 * ratio + k2 * length))
    """
    if not text:
        return 0.0
    
    length = len(text)
    ratio = length / max(original_size_bytes, 1)
    
    # k1: weight for text-to-file-size ratio (helps detect image-only PDFs)
    # k2: weight for total character volume (helps detect very small/junk files)
    k1 = 20.0  # ratio of 0.05 (good PDF) gives ~0.63 confidence from ratio alone
    k2 = 0.0002  # length of 5000 chars gives ~0.63 confidence from length alone
    
    # Combined score using exponential saturation
    score = 1.0 - (2.71828 ** -(k1 * ratio + k2 * length))
    
    return round(score, 2)

def extract_text(file_path):
    """
    Extracts raw text from PDF, DOCX, or Markdown files.
    Returns: dict { "text": str, "confidence": float, "warnings": list }
    """
    path = Path(file_path)
    extension = path.suffix.lower()
    file_size = path.stat().st_size
    
    result = {
        "text": "",
        "confidence": 0.0,
        "warnings": []
    }

    try:
        if extension == '.pdf':
            result["text"] = _extract_from_pdf(file_path)
        elif extension == '.docx':
            result["text"] = _extract_from_docx(file_path)
        elif extension == '.md':
            result["text"] = _extract_from_md(file_path)
        else:
            result["warnings"].append(f"Unexpected extension: {extension}")
            return result

        result["text"] = _normalize_text(result["text"])
        
        if not result["text"]:
            result["warnings"].append("No text could be extracted.")
        
        result["confidence"] = _calculate_confidence(result["text"], file_size)
        
        if result["confidence"] < 0.4:
            result["warnings"].append("Low extraction confidence - check for images or complex formatting.")

    except Exception as e:
        result["warnings"].append(f"Extraction error: {str(e)}")
        result["confidence"] = 0.0

    return result

def _extract_from_pdf(file_path):
    text = ""
    with fitz.open(file_path) as doc:
        for page in doc:
            # Preservation of layout hints
            page_text = page.get_text("text")
            text += page_text + "\n\n"
    return text

def _extract_from_docx(file_path):
    doc = Document(file_path)
    # Preserve paragraph structure
    return "\n\n".join([para.text for para in doc.paragraphs if para.text.strip()])

def _extract_from_md(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()
