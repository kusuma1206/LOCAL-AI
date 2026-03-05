from .input_guardrail import InputGuardrail
from .injection_guardrail import InjectionGuardrail
from .retrieval_guardrail import RetrievalGuardrail
from .context_guardrail import ContextGuardrail
from .output_guardrail import OutputGuardrail
from .semantic_relevance_guardrail import SemanticRelevanceGuardrail
from .citation_guardrail import CitationGuardrail
from .hallucination_guardrail import HallucinationGuardrail
from .confidence_scorer import ConfidenceScorer

class GuardrailManager:
    """
    Manager class that orchestrates multiple guardrails in a RAG pipeline.
    """
    def __init__(self):
        self.input_gr = InputGuardrail()
        self.injection_gr = InjectionGuardrail()
        self.retrieval_gr = RetrievalGuardrail()
        self.context_gr = ContextGuardrail()
        self.output_gr = OutputGuardrail()
        self.semantic_gr = SemanticRelevanceGuardrail()
        self.citation_gr = CitationGuardrail()
        self.hallucination_gr = HallucinationGuardrail()
        self.confidence_scorer = ConfidenceScorer()

    def check_input_pipeline(self, query: str, query_embedding: list = None, document_embeddings: list = None) -> tuple[bool, str]:
        """
        Runs input-side guardrails: validation, injection detection, and semantic relevance.
        
        Args:
            query (str): The user query.
            query_embedding (list, optional): Embedding of the query.
            document_embeddings (list, optional): Embeddings of candidate documents for relevance check.

        Returns:
            tuple[bool, str]: (True, message) if safe, (False, error_message) otherwise.
        """
        # 1. Validate query (length, empty, banned phrases)
        is_valid, msg = self.input_gr.validate_query(query)
        if not is_valid:
            return False, f"Input Validation Failed: {msg}"

        # 2. Detect prompt injection
        if not self.injection_gr.detect_injection(query):
            return False, "Prompt Injection Detected: Query contains suspicious patterns."

        # 3. Semantic Relevance Check (if embeddings are provided)
        if query_embedding is not None and document_embeddings is not None:
            is_relevant, msg = self.semantic_gr.check_relevance(query_embedding, document_embeddings)
            if not is_relevant:
                return False, f"Semantic Relevance Failed: {msg}"

        return True, "Input passed all guardrails."

    def check_retrieval_pipeline(self, results: list) -> tuple[bool, list, str]:
        """
        Runs retrieval-side guardrails: similarity check and context limiting.
        
        Returns:
            tuple[bool, list, str]: (Success, filtered_chunks, message)
        """
        # 3. Check similarity scores
        if not self.retrieval_gr.check_similarity(results):
            return False, [], "Retrieval Failed: No highly relevant documents found."

        # Filter top-k
        top_results = self.retrieval_gr.filter_top_k(results)

        # 4. Limit context (chunks and tokens)
        filtered_chunks = self.context_gr.limit_context(top_results)
        
        return True, filtered_chunks, "Retrieval passed all guardrails."

    def check_output_pipeline(self, response: str, response_embedding: list = None, context_embeddings: list = None) -> tuple[bool, str, str]:
        """
        Runs output-side guardrails: validation, cleaning, citation check, and hallucination check.
        
        Args:
            response (str): The model's response.
            response_embedding (list, optional): Embedding of the response.
            context_embeddings (list, optional): Embeddings of retrieved context chunks.

        Returns:
            tuple[bool, str, str]: (Success, cleaned_response, message)
        """
        # 5. Validate response (length, banned words)
        if not self.output_gr.validate_response(response):
            return False, response, "Output Validation Failed: Response rejected by guardrail."

        # 6. Check citations
        is_cited, cite_msg = self.citation_gr.validate_citations(response)
        if not is_cited:
            return False, response, f"Citation Error: {cite_msg}"

        # 7. Hallucination Check (if embeddings are provided)
        if response_embedding is not None and context_embeddings is not None:
            if not self.hallucination_gr.check_hallucination(response_embedding, context_embeddings):
                return False, response, "Hallucination Detected: Response is not semantically grounded in context."

        # Clean response
        cleaned_response = self.output_gr.clean_response(response)
        
        return True, cleaned_response, "Output passed all guardrails."

    def get_confidence_score(self, retrieval_results: list, answer_context_similarity: float) -> float:
        """
        Computes the final confidence score for the RAG response.
        
        Args:
            retrieval_results (list): The list of chunks used for the response.
            answer_context_similarity (float): The semantic similarity between answer and context.
            
        Returns:
            float: Confidence score in range [0, 1].
        """
        return self.confidence_scorer.calculate_score(retrieval_results, answer_context_similarity)
