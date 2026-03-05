import numpy as np

class HallucinationGuardrail:
    """
    Guardrail to detect potential hallucinations by comparing LLM responses with retrieved context.
    """
    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold

    def check_hallucination(self, response_embedding: list, context_embeddings: list) -> bool:
        """
        Computes semantic similarity between the generated response and context chunks.
        
        Args:
            response_embedding (list): Embedding vector for the model response.
            context_embeddings (list): A list of embedding vectors for the retrieved context chunks.
            
        Returns:
            bool: True if safe (no hallucination), False otherwise.
        """
        if not response_embedding or not context_embeddings:
            print("HallucinationGuardrail: Missing embeddings for check.")
            return False

        # Convert to numpy arrays
        r_vec = np.array(response_embedding)
        c_vecs = np.array(context_embeddings)

        # Compute cosine similarity (assuming normalized vectors)
        similarities = np.dot(c_vecs, r_vec)
        
        # We check if the response is semantically grounded in *any* of the context chunks
        max_similarity = np.max(similarities) if similarities.size > 0 else 0.0

        if max_similarity < self.threshold:
            print(f"HallucinationGuardrail: Potential hallucination detected. Max similarity {max_similarity:.2f} below {self.threshold}.")
            return False

        return True
