import os
import hashlib

def build_metadata(chunks, pipeline_context):
    """
    Enriches chunks with source, structural, quality, and semantic metadata.
    pipeline_context should contain: file_path, file_type, extraction_confidence, noise_reduction_percent
    """
    if not chunks:
        return []

    file_path = pipeline_context.get("file_path", "unknown")
    file_name = os.path.basename(file_path)
    file_type = pipeline_context.get("file_type", "unknown")
    
    # Use provided document ID
    document_id = pipeline_context.get("document_id", "unknown")
    
    enriched_chunks = []
    
    for i, chunk in enumerate(chunks):
        content = chunk.get("chunk_text", "")
        section_title = chunk.get("section_title", "unknown")
        
        # In the new chunker, it explicitly flags headings
        chunk_meta = chunk.get("metadata", {})
        is_heading_explicit = chunk_meta.get("is_explicit_heading")
        
        is_heading = False
        content_clean = content.replace(f"[{section_title}]", "").strip()
        
        if is_heading_explicit is not None:
            is_heading = is_heading_explicit
        else:
            # Fallback for old chunker format
            if not content_clean or content_clean == section_title:
                is_heading = True
            elif len(content_clean.split()) < 20 and content_clean == content_clean.upper():
                is_heading = True
            
        word_count = len(content_clean.split())
        char_count = len(content_clean)
        
        # New semantic metadata fields
        document_name = file_name
        parent_section = "unknown" # Parent section parsing could be added later
        
        metadata = {
            "document_id": document_id,
            "document_name": document_name,
            "file_type": file_type,
            "section_title": section_title,
            "parent_section": parent_section,
            "chunk_position": i,
            "chunk_index": i,
            "is_heading": is_heading,
            "chunk_length": char_count,
            "extraction_confidence": pipeline_context.get("extraction_confidence", 0.0),
            "noise_reduction_percent": pipeline_context.get("noise_reduction_percent", 0.0),
            "word_count": word_count,
            "character_count": char_count
        }
        
        enriched_chunks.append({
            "chunk_text": content,
            "is_heading": is_heading,
            "chunk_index": i,
            "section_title": section_title, # Pass these down for main.py storage
            "document_id": document_id,
            "document_name": document_name,
            "parent_section": parent_section,
            "metadata": metadata
        })
        
    return enriched_chunks
