import re

def generate_section_summary(text: str) -> str:
    """
    Generate an intelligent summary. For large texts (Global Summaries), 
    uses a 'Drip-Fed' strategy (Beginning + Middle + End) to capture the full scope.
    """
    if not text or len(text) < 100:
        return text or "Structural node"

    # Normalize whitespace
    clean_text = re.sub(r'\s+', ' ', text).strip()
    
    # Strategy: If text is long (> 3000 chars), take samples from Begin, Middle, and End
    if len(clean_text) > 3000:
        print(f"  [Summarizer] Large text detected ({len(clean_text)} chars). Applying Drip-Fed strategy...")
        # Take first 1000, middle 800, and last 800
        start_fragment = clean_text[:1000]
        mid_point = len(clean_text) // 2
        mid_fragment = clean_text[mid_point-400 : mid_point+400]
        end_fragment = clean_text[-1000:]
        
        # Combine fragments for the summarization window
        representative_text = f"{start_fragment} ... {mid_fragment} ... {end_fragment}"
    else:
        representative_text = clean_text

    # Extract sentences from the representative text
    sentences = re.split(r'(?<=[.!?]) +', representative_text)
    
    # Take first 3-4 sentences of the representative content
    candidate_summary = " ".join(sentences[:4])[:400]

    # --- Quality Gate ---
    alpha_chars = sum(1 for c in candidate_summary if c.isalpha())
    alpha_ratio = alpha_chars / len(candidate_summary) if candidate_summary else 0
    
    is_valid = (
        len(candidate_summary) >= 30 and
        len(candidate_summary.split()) >= 5 and
        alpha_ratio >= 0.6
    )

    if is_valid:
        print("  [Summarizer] Summary accepted")
        return candidate_summary
    else:
        print("  [Summarizer] Summary rejected — fallback applied")
        # Fallback to first 250 characters of representative text
        return representative_text[:250]