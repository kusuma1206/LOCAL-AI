import numpy as np

class ConfidenceScorer:
    """
    Computes a confidence score for generated answers based on retrieval and alignment metrics.
    """
    def __init__(self, max_chunks: int = 5):
        self.max_chunks = max_chunks
        self.last_score = 0.0

    def calculate_score(self, retrieval_results: list, answer_context_similarity: float) -> float:
        """
        Computes a confidence score between 0 and 1.
        
        Args:
            retrieval_results (list): List of retrieval result objects/dicts with 'score'.
            answer_context_similarity (float): Similarity score between answer and context chunks.
            
        Returns:
            float: Confidence score [0, 1].
        """
        if not retrieval_results:
            self.last_score = 0.0
            return 0.0

        # 1. Retrieval Quality (Mean of retrieval scores)
        retrieval_scores = [r.get('score', 0.0) if isinstance(r, dict) else getattr(r, 'score', 0.0) for r in retrieval_results]
        mean_retrieval_score = np.mean(retrieval_scores) if retrieval_scores else 0.0

        # 2. Support Density (Ratio of chunks found vs max expected)
        chunk_count_score = min(len(retrieval_results) / self.max_chunks, 1.0)

        # 3. Answer Alignment (Directly use the similarity score)
        # Assuming answer_context_similarity is already in [0, 1] range
        alignment_score = max(min(answer_context_similarity, 1.0), 0.0)

        # Weighted aggregation (Weights can be tuned)
        # 40% retrieval quality, 20% chunk count, 40% answer alignment
        weights = [0.4, 0.2, 0.4]
        final_score = (
            (weights[0] * mean_retrieval_score) +
            (weights[1] * chunk_count_score) +
            (weights[2] * alignment_score)
        )

        self.last_score = float(final_score)
        return self.last_score

    def get_confidence_score(self) -> float:
        """
        Returns the last computed confidence score.
        """
        return self.last_score
