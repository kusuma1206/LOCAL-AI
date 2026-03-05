import numpy as np
from sentence_transformers import SentenceTransformer

# Model config
MODEL_NAME = 'all-MiniLM-L6-v2'
_model = None

def get_model():
    """Singleton pattern to load the model once."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(MODEL_NAME)
    return _model

def embed_query(query: str) -> list:
    """
    Generates a 384-dimensional normalized embedding for a given query string.
    """
    if not query:
        return []
        
    model = get_model()
    
    # Generate embedding
    raw_embedding = model.encode([query])[0]
    
    # L2 Normalization
    norm = np.linalg.norm(raw_embedding)
    if norm > 0:
        normalized_embedding = (raw_embedding / norm).tolist()
    else:
        normalized_embedding = raw_embedding.tolist()
        
    print("  [Query Embedder] Query embedded successfully")
    return normalized_embedding
