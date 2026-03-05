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

def chunk_text(sections, chunk_size=500, overlap=50):
    """
    Enforces Structural Integrity: atomic headings, safe boundaries, and anchoring.
    """
    if not sections:
        return []

    all_chunks = []

    for section in sections:
        title = section["section_title"]
        content = section["content"]
        
        if not content: continue
            
        # RULE 1: Heading Anchoring - Every chunk starts with its context
        # RULE 2: Split only at Paragraph Boundaries (\n\n)
        paragraphs = [p.strip() for p in re.split(r'\n\s*\n', content) if p.strip()]
        
        current_chunk_parts = [f"[{title}]"]
        current_chunk_len = len(current_chunk_parts[0])
        
        for i, para in enumerate(paragraphs):
            # Check if adding para exceeds size
            if current_chunk_len + len(para) > chunk_size:
                # If we have content, save it
                if len(current_chunk_parts) > 1:
                    combined = "\n\n".join(current_chunk_parts)
                    all_chunks.append({
                        "chunk_text": combined,
                        "section_title": title,
                        "metadata": {"length": len(combined)}
                    })
                    # Start new chunk with heading anchoring
                    current_chunk_parts = [f"[{title}]", para]
                    current_chunk_len = len(current_chunk_parts[0]) + len(para) + 2
                else:
                    # Paragraph itself is too big - split by sentence
                    splitted_sub_chunks = _split_para_by_sentences(para, chunk_size, title)
                    for sub in splitted_sub_chunks:
                        all_chunks.append({
                            "chunk_text": sub,
                            "section_title": title,
                            "metadata": {"length": len(sub)}
                        })
                    current_chunk_parts = [f"[{title}]"]
                    current_chunk_len = len(current_chunk_parts[0])
            else:
                current_chunk_parts.append(para)
                current_chunk_len += len(para) + 2 # +2 for \n\n

        # Final part of section
        if len(current_chunk_parts) > 1:
            combined = "\n\n".join(current_chunk_parts)
            all_chunks.append({
                "chunk_text": combined,
                "section_title": title,
                "metadata": {"length": len(combined)}
            })

    return all_chunks
