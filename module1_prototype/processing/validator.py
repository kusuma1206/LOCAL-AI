import os
import hashlib
import json
import magic
import fitz  # PyMuPDF
from docx import Document
from pathlib import Path
from config import settings

ALLOWED_MIME_TYPES = {
    'application/pdf': 'PDF',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'DOCX',
    'text/markdown': 'Markdown',
    'text/plain': 'Markdown'  # Often MD files are seen as plain text
}

def compute_file_hash(file_path):
    """Computes SHA-256 hash of file content."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def check_duplicate(hash_value):
    """Checks if hash exists in local JSON registry."""
    registry_path = Path(settings.DUPLICATE_REGISTRY_PATH)
    if not registry_path.exists():
        # Create empty registry if missing
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        with open(registry_path, "w") as f:
            json.dump({}, f)
        return False

    with open(registry_path, "r") as f:
        try:
            registry = json.load(f)
        except json.JSONDecodeError:
            registry = {}
            
    return hash_value in registry

def detect_pdf_risks(file_path):
    """
    Detects encrypted or scanned PDFs.
    Returns: (warnings, is_scanned_suspicion)
    """
    warnings = []
    is_scanned_suspicion = False
    try:
        with fitz.open(file_path) as doc:
            page_count = len(doc)
            if doc.is_encrypted:
                warnings.append("PDF is encrypted and may require a password for full processing.")
            
            # Check for scanned PDF (low text volume across first 3 pages)
            total_preview_text = ""
            for i in range(min(3, page_count)):
                total_preview_text += doc[i].get_text()
            
            text_length = len(total_preview_text.strip())
            
            if text_length < settings.SCANNED_PDF_THRESHOLD and page_count > 1:
                is_scanned_suspicion = True
                warnings.append("OCR recommended — low extractable text")
            elif text_length == 0 and page_count == 1:
                # Single page with 0 text is just empty, handled by semantic check
                pass

    except Exception as e:
        warnings.append(f"Risk detection partially failed: {str(e)}")
    
    return warnings, is_scanned_suspicion

def check_semantic_content(file_path, is_pdf_scanned_suspicion=False):
    """
    Performs a lightweight check to ensure the document has extractable text.
    Returns: (bool, str) - (has_content, message)
    """
    path = Path(file_path)
    extension = path.suffix.lower()
    text_preview = ""

    # If it's a PDF we already suspect is scanned, we skip the hard failure here
    # to allow the pipeline to proceed with a warning instead.
    if is_pdf_scanned_suspicion:
        return True, "Suspected scanned PDF (passed semantic check for warning path)."

    try:
        if extension == '.pdf':
            with fitz.open(file_path) as doc:
                for i in range(min(2, len(doc))):
                    text_preview += doc[i].get_text()
                    if text_preview.strip():
                        break
        
        elif extension == '.docx':
            doc = Document(file_path)
            for i, para in enumerate(doc.paragraphs):
                text_preview += para.text
                if text_preview.strip() or i > 10:
                    break
        
        elif extension == '.md':
            with open(file_path, 'r', encoding='utf-8') as f:
                text_preview = f.read(1000)
        
        if not text_preview.strip():
            return False, "Document contains no extractable semantic content."
            
        return True, "Semantic content confirmed."

    except Exception as e:
        return False, f"Semantic content check failed: {str(e)}"

def validate_document(file_path):
    """
    Performs production-grade validation on a document.
    Returns a structured dictionary with status, message, and warnings.
    """
    path = Path(file_path)
    result = {
        "status": "VALID",
        "message": "Document is valid.",
        "warnings": []
    }

    # 1. File Integrity Checks
    if not path.exists():
        result.update({"status": "INVALID", "message": f"File not found: {file_path}"})
        return result

    if not path.is_file():
        result.update({"status": "INVALID", "message": f"Path is not a file: {file_path}"})
        return result

    if not os.access(file_path, os.R_OK):
        result.update({"status": "INVALID", "message": f"File is not readable: {file_path}"})
        return result

    file_size = path.stat().st_size
    if file_size == 0:
        result.update({"status": "INVALID", "message": "File is empty."})
        return result

    if file_size < settings.MIN_FILE_SIZE:
        result.update({"status": "INVALID", "message": f"File is too small ({file_size} bytes). Minimum: {settings.MIN_FILE_SIZE} bytes."})
        return result

    # 2. MIME Type Validation
    try:
        mime = magic.Magic(mime=True)
        detected_mime = mime.from_file(file_path)
        
        if detected_mime not in ALLOWED_MIME_TYPES:
            if path.suffix.lower() == '.md' and detected_mime == 'text/plain':
                pass # Allow
            else:
                result.update({
                    "status": "INVALID", 
                    "message": f"Unsupported MIME type: {detected_mime}. Supported: PDF, DOCX, Markdown."
                })
                return result
    except Exception as e:
        result["warnings"].append(f"MIME validation warning: {str(e)}")

    # 3. File Size Sanity Check
    if file_size > settings.MAX_FILE_SIZE:
        result["status"] = "VALID_WITH_WARNING"
        result["warnings"].append(f"File size is large ({file_size / 1024 / 1024:.2f} MB). Processing might be slow.")

    # Create stable deterministic UUID from file hash
    import uuid
    file_hash = compute_file_hash(file_path)
    # Using a fixed namespace for deterministic UUIDs across different runs/environments
    NAMESPACE_LOCAL_AI = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8') # DNS namespace as base
    document_id = str(uuid.uuid5(NAMESPACE_LOCAL_AI, file_hash))
    result["document_id"] = document_id

    # 4. Duplicate Detection (using full hash)
    try:
        if check_duplicate(file_hash):
            result.update({
                "status": "DUPLICATE_DETECTED",
                "message": "This file has already been processed (duplicate hash detected)."
            })
            return result
    except Exception as e:
        result["warnings"].append(f"Duplicate detection failed: {str(e)}")

    # 5. Risk Detection & Semantic Check
    is_pdf_scanned_suspicion = False
    if path.suffix.lower() == '.pdf':
        risk_warnings, is_pdf_scanned_suspicion = detect_pdf_risks(file_path)
        if risk_warnings:
            if is_pdf_scanned_suspicion:
                result["status"] = "VALID_WITH_WARNING"
                result["message"] = "Scanned or image-based PDF detected."
            result["warnings"].extend(risk_warnings)

    # 6. Semantic Content Validation
    has_content, content_msg = check_semantic_content(file_path, is_pdf_scanned_suspicion)
    if not has_content:
        result.update({
            "status": "INVALID",
            "message": content_msg
        })
        return result

    return result
