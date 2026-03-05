import re

def _is_tech_content(line):
    """Detects URLs, Emails, and Code-like syntax to prevent accidental removal."""
    # URLs
    if re.search(r'https?://|www\.', line):
        return True
    # Emails
    if re.search(r'[\w\.-]+@[\w\.-]+\.\w+', line):
        return True
    # Code clusters (assignments, brackets, semi-colons)
    if re.search(r'[\w\]\s]=\s|[\{\}]|;\s*$', line):
        return True
    return False

def _is_symbol_noise(line):
    """Heuristic to detect decorative symbol clusters or separators."""
    if len(line) < 5:
        return False
        
    if _is_tech_content(line):
        return False
        
    alpha_count = sum(1 for c in line if c.isalpha())
    alpha_density = alpha_count / len(line)
    
    # Flag if alphabetic content is low (< 40%) AND contains 3+ consecutive symbols
    if alpha_density < 0.4 and re.search(r'[^a-zA-Z0-9\s]{3,}', line):
        return True
        
    return False

def clean_text(text):
    """
    Advanced noise suppression with observability metrics and tech-integrity guards.
    Returns: dict { "cleaned_text": str, "lines_removed": int, "noise_reduction_percent": float }
    """
    if not text:
        return {"cleaned_text": "", "lines_removed": 0, "noise_reduction_percent": 0.0}
    
    original_length = len(text)
    
    # 1. Whitespace Normalization
    text = re.sub(r'[ \t]+', ' ', text)
    
    lines = text.split('\n')
    original_line_count = len(lines)
    
    # 2. Heuristic-Based Filtering pipeline
    filtered_lines = []
    line_freq = {}
    
    # Pass 1: Frequency Analysis for deduplication (headers/footers)
    for line in lines:
        raw_l = line.strip()
        if raw_l and len(raw_l) > 10: 
            line_freq[raw_l] = line_freq.get(raw_l, 0) + 1
            
    # Pass 2: Cleaning
    seen_in_current_pass = set()
    for line in lines:
        raw_line = line.strip()
        
        # Preserve paragraph structure
        if not raw_line:
            filtered_lines.append("")
            continue
            
        # a) Page numbers removal
        if re.match(r'^(page\s+\d+|\d+\s+of\s+\d+|\d+)$', raw_line, re.IGNORECASE):
            continue
            
        # b) Numeric-only line removal
        if re.sub(r'[\.\s\-\(\)]', '', raw_line).isdigit() and len(raw_line) < 15:
            continue
            
        # c) Symbol-heavy filtering (Refined Heuristic)
        if _is_symbol_noise(raw_line):
            continue
            
        # d) Meaningless short lines
        if len(raw_line) < 3 and not re.match(r'^[\-\*\d•]', raw_line):
            continue
            
        # e) Repetition Suppression (Frequency Analysis)
        if line_freq.get(raw_line, 0) > 2:
            if raw_line in seen_in_current_pass:
                continue
            seen_in_current_pass.add(raw_line)
            
        filtered_lines.append(raw_line)

    # 3. Final Reconstruction
    cleaned_text = "\n".join(filtered_lines)
    cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text).strip()
    
    cleaned_length = len(cleaned_text)
    lines_removed = original_line_count - len([l for l in filtered_lines if l.strip()])
    
    reduction = 0.0
    if original_length > 0:
        reduction = ((original_length - cleaned_length) / original_length) * 100
        
    return {
        "cleaned_text": cleaned_text,
        "lines_removed": max(0, lines_removed),
        "noise_reduction_percent": round(reduction, 2)
    }
