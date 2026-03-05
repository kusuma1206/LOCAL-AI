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
        
        # Calculate semantic attributes
        word_count = len(content.split())
        char_count = len(content)
        
        metadata = {
            # 1. Source Metadata
            "document_id": document_id,
            "file_name": file_name,
            "file_type": file_type,
            
            # 2. Structural Metadata
            "section_title": section_title,
            "chunk_position": i,
            "chunk_length": char_count,
            
            # 3. Quality Signals
            "extraction_confidence": pipeline_context.get("extraction_confidence", 0.0),
            "noise_reduction_percent": pipeline_context.get("noise_reduction_percent", 0.0),
            
            # 4. Semantic Attributes
            "word_count": word_count,
            "character_count": char_count
        }
        
        enriched_chunks.append({
            "chunk_text": content,
            "metadata": metadata
        })
        
    return enriched_chunks
