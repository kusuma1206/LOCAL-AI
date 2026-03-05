import re

def _get_alpha_density(line):
    """Calculates the ratio of alphabetic characters to total characters."""
    if not line:
        return 0.0
    alpha_count = sum(1 for c in line if c.isalpha())
    return alpha_count / len(line)

def _is_separator(line):
    """Detects visual separator lines like ---, ===, ***."""
    return re.match(r'^[\-\=\*\_]{3,}$', line) is not None

GENERIC_LABELS = {
    'Actions', 'Note', 'Notes', 'Steps', 'Metadata', 'Example', 'Examples', 
    'Description', 'Overview', 'Status', 'Draft', 'Review', 'Characteristics'
}

def _is_explicit_signal(line):
    """Detects Markdown headings and numbered/labeled sections with hierarchy awareness."""
    # Major Markdown (H1-H2)
    if re.match(r'^#{1,2}\s+.+', line):
        return True, 1
    # Minor Markdown (H3-H6)
    if re.match(r'^#{3,6}\s+.+', line):
        return True, 2
        
    # Major Numbering (1., 2., etc. but NOT 1.1)
    if re.match(r'^\d+\.\s+[A-Z].+', line):
        return True, 1
        
    # Minor/Deep Numbering (1.1, 1.1.1, etc.)
    if re.match(r'^(\d+\.)+\d+\s+[A-Z].+', line):
        return True, 2
        
    # Labels (Key Terms: Abstract:)
    if re.match(r'^[A-Z][a-z\s]{2,15}:\s*$', line):
        clean_label = line.strip(':').strip()
        if clean_label in GENERIC_LABELS:
            return False, 0
        return True, 2 # Labels are usually minor
        
    return False, 0

def _is_visual_signal(line):
    """Detects ALL CAPS and separators."""
    if not line:
        return False, 0
        
    if _is_separator(line):
        return True, 1
        
    # ALL CAPS lines (Short, likely a heading)
    if line.isupper() and 3 < len(line) < 60 and _get_alpha_density(line) > 0.6:
        # Refinement: Reject enum-like status labels or workflow states
        if '_' in line or ' ' not in line:
            return False, 0
            
        # Avoid lines that end in typical sentence punctuation
        if not line.endswith(('.', '?', '!', ':')):
            return True, 2 # Visual signals (all caps) are treated as minor unless keywords match
            
    return False, 0

def _is_linguistic_signal(line):
    """Detects major transition keywords."""
    major_keywords = ['Summary', 'Conclusion', 'Introduction', 'Appendix', 'References', 'Methodology', 'Results']
    pattern = r'^(' + '|'.join(major_keywords) + r')[:\s]*$'
    if re.match(pattern, line, re.IGNORECASE):
        return True, 1
    return False, 0

def _apply_fallback_segmentation(text):
    """
    Splits text every 800-1000 characters, attempting to break at sentence boundaries.
    Ensures each section has at least 300 characters.
    """
    sections = []
    start = 0
    total_len = len(text)
    section_num = 1

    while start < total_len:
        # Target end is between 800 and 1000 chars from start
        target_max = start + 1000
        
        # If remaining text is small, just take it all
        if total_len - start <= 1000:
            end = total_len
        else:
            # Search for sentence boundaries in [800, 1000] range
            search_start = start + 800
            search_range = text[search_start:target_max]
            
            # Find last sentence-ending punctuation followed by space or newline
            match = None
            for m in re.finditer(r'[\.\!\?][\s\n]', search_range):
                match = m
            
            if match:
                end = search_start + match.end()
            else:
                # No sentence boundary found, split at 1000
                end = target_max

        segment_content = text[start:end].strip()
        
        # Ensure minimum 300 characters (except for the last section)
        if len(segment_content) < 300 and sections and end == total_len:
            # Merge with previous section if it's the last one and too small
            sections[-1]["content"] += "\n\n" + segment_content
        else:
            sections.append({
                "section_title": f"Section {section_num}",
                "content": segment_content
            })
            section_num += 1
            
        start = end

    print(f"Fallback segmentation applied. Created {len(sections)} synthetic sections.")
    return sections

def analyze_structure(text):
    """
    Hierarchical Structure Intelligence: segments text into macro nodes.
    Minor headings and sub-sections are folded into their parent major sections.
    """
    if not text:
        return []

    lines = text.split('\n')
    sections = []
    current_section_title = "Initial Segment"
    current_section_content = []
    
    # Hierarchy State
    last_major_number = 0

    for i, line in enumerate(lines):
        raw_line = line.strip()
        if not raw_line:
            if current_section_content:
                current_section_content.append("")
            continue

        is_heading = False
        level = 0
        
        # 1. Heading Detection with Level Awareness
        sig_exp, lev_exp = _is_explicit_signal(raw_line)
        sig_vis, lev_vis = _is_visual_signal(raw_line)
        sig_lin, lev_lin = _is_linguistic_signal(raw_line)
        
        if sig_lin:
            is_heading, level = True, lev_lin
        elif sig_exp:
            is_heading, level = True, lev_exp
        elif sig_vis:
            is_heading, level = True, lev_vis

        # 2. Hierarchy Enforcement
        # Numbered major heading check (Progression)
        num_match = re.match(r'^(\d+)\.\s+', raw_line)
        if level == 1 and num_match:
            current_num = int(num_match.group(1))
            # If numbering resets (e.g. 6. -> 1.), it's likely a sub-list or nested content
            if current_num <= last_major_number and last_major_number > 0:
                level = 2 # Downgrade to minor
            else:
                last_major_number = current_num

        # 3. Decision: New Section or Append
        if is_heading and level == 1:
            # Save previous section
            if current_section_content:
                sections.append({
                    "section_title": current_section_title,
                    "content": "\n".join(current_section_content).strip()
                })
            
            # Start new major section
            clean_title = re.sub(r'^#{1,6}\s*', '', raw_line)
            clean_title = re.sub(r'[:\.]$', '', clean_title).strip()
            
            if _is_separator(raw_line):
                current_section_title = "Next Section"
            else:
                current_section_title = clean_title
                
            current_section_content = []
        else:
            # Fold everything else (text, minor headings, generic labels) into content
            current_section_content.append(line)

    # Append final section
    if current_section_content or current_section_title != "Initial Segment":
        sections.append({
            "section_title": current_section_title,
            "content": "\n".join(current_section_content).strip()
        })

    if not sections:
        sections = [{"section_title": "Main Content", "content": text.strip()}]

    # Fallback Segmentation for Large Unstructured Documents
    if len(sections) == 1 and sections[0]["section_title"] == "Initial Segment" and len(text) > 1500:
        sections = _apply_fallback_segmentation(text)

    return sections

def get_structure_report(sections, total_text_length):
    """
    Analyzes detected sections for quality and anomalies.
    Returns: dict { "summary": dict, "warnings": list, "distribution": list }
    """
    if not sections:
        return {"summary": {}, "warnings": ["No sections detected."], "distribution": []}

    lengths = [len(s["content"]) for s in sections]
    count = len(sections)
    avg_len = sum(lengths) / count if count > 0 else 0
    
    report = {
        "summary": {
            "total_sections": count,
            "avg_section_length": round(avg_len, 1),
            "max_section_length": max(lengths),
            "min_section_length": min(lengths)
        },
        "warnings": [],
        "distribution": [{"title": s["section_title"], "len": len(s["content"])} for s in sections]
    }

    # 1. Under-segmentation Signal
    if count == 1 and total_text_length > 1500:
        report["warnings"].append("Under-segmentation: Large document treated as single section.")

    # 2. Over-segmentation Signal
    tiny_sections = [s for s in report["distribution"] if s["len"] < 50]
    if count > 10 and avg_len < 150:
        report["warnings"].append(f"Over-segmentation suspected: {count} sections with low average length.")

    # 3. Tiny Section Detection
    if tiny_sections and count > 1:
        report["warnings"].append(f"Detected {len(tiny_sections)} tiny sections (< 50 chars).")

    return report
