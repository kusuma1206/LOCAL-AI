import re

def _split_para_by_sentences(para, chunk_size, title):
    """Splits a large paragraph by sentence boundaries to fit chunk_size."""
    sentences = re.split(r'(?<=[.!?])\s+', para)
    chunks = []
    current_parts = [f"[{title}]"] # Anchoring
    current_len = len(current_parts[0])
    
    for sent in sentences:
        if current_len + len(sent) > chunk_size and len(current_parts) > 1:
            # Yield current chunk
            chunks.append(" ".join(current_parts))
            current_parts = [f"[{title}]", sent] # Continuity anchoring
            current_len = sum(len(p) for p in current_parts) + 1
        else:
            current_parts.append(sent)
            current_len += len(sent) + 1
            
    if len(current_parts) > 1:
        chunks.append(" ".join(current_parts))
    return chunks

def _chunk_paragraphs(content, title):
    """Splits section content by paragraphs to create semantic chunks."""
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', content) if p.strip()]
    chunks = []
    
    for para in paragraphs:
        # Avoid extremely tiny isolated paragraphs unless they are rich
        if len(para.split()) < 5:
            # We can prefix with title if it's too short to float alone
            chunks.append(f"[{title}] {para}")
        else:
            chunks.append(para)
            
    return chunks

def chunk_text(sections, chunk_size=1500, overlap=0):
    """
    Semantic Structure-Aware Chunking: 
    - Treats each structural section heading as its own precise chunk.
    - Treats each paragraph within the section as its own natural chunk.
    - Discards arbitrary token/character sizing.
    """
    if not sections:
        return []

    all_chunks = []

    for section in sections:
        title = section["section_title"]
        content = section["content"]
        
        # 1. Yield the section title as a true heading chunk
        all_chunks.append({
            "chunk_text": title,
            "section_title": title,
            "metadata": {"length": len(title), "is_explicit_heading": True}
        })
        
        if not content: continue
            
        # 2. Yield each paragraph as a structural chunk
        paragraphs = _chunk_paragraphs(content, title)
        
        for para in paragraphs:
            all_chunks.append({
                "chunk_text": para,
                "section_title": title,
                "metadata": {"length": len(para), "is_explicit_heading": False}
            })

    return all_chunks
