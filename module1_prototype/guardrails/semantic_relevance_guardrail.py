import numpy as np

class SemanticRelevanceGuardrail:
    """
    Guardrail that checks semantic relevance between a query and stored document embeddings.
    """
    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold
        self.rejection_message = "Your question does not appear related to the uploaded documents."

    def check_relevance(self, query_embedding: list, document_embeddings: list) -> tuple[bool, str]:
        """
        Computes cosine similarity between query and multiple document embeddings.
        
        Args:
            query_embedding (list): The embedding vector for the user query.
            document_embeddings (list): A list of embedding vectors for candidate documents.
            
        Returns:
            tuple[bool, str]: (True, "Success") if relevant, (False, error_message) otherwise.
        """
        if not query_embedding or not document_embeddings:
            return False, self.rejection_message

        # Convert to numpy arrays for efficient computation
        q_vec = np.array(query_embedding)
        d_vecs = np.array(document_embeddings)

        # Assuming vectors are already normalized (as done in query_embedder.py)
        # Cosine similarity for normalized vectors is just the dot product
        similarities = np.dot(d_vecs, q_vec)
        
        max_similarity = np.max(similarities) if similarities.size > 0 else 0.0

        if max_similarity < self.threshold:
            print(f"SemanticRelevanceGuardrail: Max similarity {max_similarity:.2f} below threshold {self.threshold}")
            return False, self.rejection_message

        return True, "Relevant documents found."
