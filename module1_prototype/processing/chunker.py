import re

def get_words(text):
    """Splits text into words preserving basic punctuation."""
    return re.findall(r'\S+', text)

def create_hybrid_chunks(title, content, target_min=120, target_max=200, overlap=25):
    """
    Creates hybrid chunks from a section's text.
    Each chunk starts with the section heading.
    Size constraint: 120-200 words. (We will aim for target_max words per chunk).
    Overlap: 20-30 words.
    """
    if not content.strip():
        return []
        
    words = get_words(content)
    if not words:
        return []
        
    # If the total content is small, just one chunk
    if len(words) <= target_max:
        chunk_text = f"{title}\n\n{content.strip()}"
        return [chunk_text]
        
    chunks = []
    i = 0
    while i < len(words):
        # Take up to target_max words
        chunk_words = words[i:i + target_max]
        
        # Don't create tiny trailing chunks unless it's the only text left
        if len(chunk_words) < 50 and len(chunks) > 0:
            # Append remaining words to the last chunk (might exceed 200 slightly, but better than isolated tail)
            last_chunk = chunks.pop()
            # We need to rebuild the last chunk but we can't easily extract its words without the title.
            # Instead of complex merging, we allow the small tail chunk if we strictly follow the 120-200 rule,
            # or we just take the last 'target_max' words of the document.
            chunk_words = words[-target_max:] if len(words) > target_max else words
            chunk_text = f"{title}\n\n{' '.join(chunk_words)}"
            chunks.append(chunk_text)
            break
            
        chunk_text = f"{title}\n\n{' '.join(chunk_words)}"
        chunks.append(chunk_text)
        
        # Move forward by (target_max - overlap)
        step = target_max - overlap
        if step <= 0:
            step = target_max # Fallback to avoid infinite loop
        i += step
        
    # Deduplicate in case the tail logic caused duplicates
    final_chunks = []
    seen = set()
    for c in chunks:
        if c not in seen:
            seen.add(c)
            final_chunks.append(c)
            
    return final_chunks

def chunk_text(sections, chunk_size=200, overlap=25):
    """
    Hybrid Chunking: 
    - Chunk must contain heading + text
    - Length: ~120-200 words
    - Overlap: ~20-30 words
    - Never store heading-only chunks
    """
    if not sections:
        return []

    all_chunks = []

    for section in sections:
        title = section.get("section_title") or section.get("title")
        section_id = section.get("section_id")
        content = section.get("content", "")
        
        if not content or not content.strip():
            continue # Prevent heading-only chunks
            
        chunks = create_hybrid_chunks(title, content, target_max=chunk_size, overlap=overlap)
        
        for c in chunks:
            all_chunks.append({
                "chunk_text": c,
                "section_title": title,
                "section_id": section_id,
                "metadata": {
                    "length": len(c),
                    "is_explicit_heading": False
                }
            })

    return all_chunks
