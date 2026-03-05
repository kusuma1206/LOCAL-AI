class RetrievalGuardrail:
    """
    Guardrail for verifying the quality and relevance of retrieved documents.
    """
    def __init__(self, threshold: float = 0.6):
        self.threshold = threshold

    def check_similarity(self, results: list) -> bool:
        """
        Checks if the highest similarity score in retrieval results meets the threshold.
        
        Args:
            results (list): A list of dictionaries/objects containing a 'score' key.
            
        Returns:
            bool: True if the highest score >= threshold, False otherwise.
        """
        if not results:
            print("RetrievalGuardrail: No results found.")
            return False

        # Extract scores (assuming dictionaries with a 'score' key)
        # Handle cases where results might be objects by attempting to access .score
        try:
            scores = [r.get('score', 0.0) if isinstance(r, dict) else getattr(r, 'score', 0.0) for r in results]
        except Exception as e:
            print(f"RetrievalGuardrail: Error extracting scores: {e}")
            return False

        max_score = max(scores) if scores else 0.0
        
        if max_score < self.threshold:
            print(f"RetrievalGuardrail: Highest similarity score ({max_score:.2f}) is below threshold ({self.threshold}).")
            return False

        return True

    def filter_top_k(self, results: list, top_k: int = 5) -> list:
        """
        Filters and returns the top-k retrieval results.
        
        Args:
            results (list): The retrieval results.
            top_k (int): Number of top results to return.
            
        Returns:
            list: The filtered top-k results.
        """
        # Sort by score descending (if possible) before slicing
        try:
            sorted_results = sorted(
                results, 
                key=lambda x: x.get('score', 0.0) if isinstance(x, dict) else getattr(x, 'score', 0.0), 
                reverse=True
            )
            return sorted_results[:top_k]
        except Exception as e:
            print(f"RetrievalGuardrail: Warning during sorting: {e}")
            return results[:top_k]
