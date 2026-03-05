import numpy as np
from datetime import datetime
from sentence_transformers import SentenceTransformer

# Model config
MODEL_NAME = 'all-MiniLM-L6-v2'
EXPECTED_DIM = 384

_model = None

def get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        print(f"Loading SentenceTransformer: {MODEL_NAME}")
        _model = SentenceTransformer(MODEL_NAME)
    return _model

def _get_alpha_density(text):
    if not text: return 0.0
    alphas = sum(1 for c in text if c.isalpha())
    return alphas / len(text)

def generate_embeddings(enriched_chunks):
    """
    Embedding Intelligence Engine: gates, generates, and normalizes vectors.
    Returns: List of enriched chunks with 'embedding' and updated 'metadata'.
    """
    if not enriched_chunks:
        return []
        
    model = get_model()
    processed_chunks = []
    
    # 1. Quality Gating & Pre-processing
    texts_to_embed = []
    valid_chunks = []
    
    for chunk in enriched_chunks:
        text = chunk.get("chunk_text", "").strip()
        
        # Gating rules
        if len(text) < 20:
            # print(f"  [Gating] Skipped tiny chunk: {repr(text[:20])}...")
            continue
        if _get_alpha_density(text) < 0.2:
            # print(f"  [Gating] Skipped noise-heavy chunk: {repr(text[:20])}...")
            continue
            
        texts_to_embed.append(text)
        valid_chunks.append(chunk)

    if not texts_to_embed:
        print("Embedder: No valid chunks passed quality gating.")
        return []

    print(f"Generating and normalizing embeddings for {len(texts_to_embed)}/{len(enriched_chunks)} chunks...")
    
    # 2. Generation
    raw_embeddings = model.encode(texts_to_embed)
    
    # 3. Normalization (L2)
    norms = np.linalg.norm(raw_embeddings, axis=1, keepdims=True)
    normalized_embeddings = raw_embeddings / norms
    
    # 4. Enrichment & Failure Detection
    timestamp = datetime.now().isoformat()
    
    for i, chunk in enumerate(valid_chunks):
        embedding = normalized_embeddings[i].tolist()
        
        # Dimension Check
        if len(embedding) != EXPECTED_DIM:
            print(f"Embedder Error: Dimension mismatch for chunk {i}. Got {len(embedding)}, expected {EXPECTED_DIM}")
            continue
            
        # Update Metadata
        metadata = chunk.get("metadata", {})
        metadata.update({
            "embedding_model": MODEL_NAME,
            "embedding_dimension": EXPECTED_DIM,
            "embedding_timestamp": timestamp
        })
        
        chunk["embedding"] = embedding
        processed_chunks.append(chunk)

    return processed_chunks
