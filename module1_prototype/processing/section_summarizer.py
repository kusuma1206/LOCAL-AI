import re

def generate_section_summary(section_text: str) -> str:
    """
    Generate a lightweight rule-based summary with a quality gate.
    """
    if not section_text:
        return ""

    # Normalize whitespace
    clean_text = re.sub(r'\s+', ' ', section_text).strip()

    # Strategy: First 2–3 sentences
    sentences = re.split(r'(?<=[.!?]) +', clean_text)
    candidate_summary = " ".join(sentences[:3])[:300]

    # --- Quality Gate ---
    alpha_chars = sum(1 for c in candidate_summary if c.isalpha())
    alpha_ratio = alpha_chars / len(candidate_summary) if candidate_summary else 0
    
    is_valid = (
        len(candidate_summary) >= 30 and
        len(candidate_summary.split()) >= 5 and
        alpha_ratio >= 0.6
    )

    if is_valid:
        print("  [Section Summarizer] Section summary accepted")
        return candidate_summary
    else:
        print("  [Section Summarizer] Section summary rejected — fallback applied")
        # Fallback to first 250 characters of original text
        return clean_text[:250]