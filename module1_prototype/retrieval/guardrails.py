import re

class GuardrailEngine:
    def __init__(self):
        # PII Patterns
        self.email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
        self.phone_pattern = re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b')
        
        # Prompt Injection Keywords
        self.injection_keywords = [
            "ignore previous instructions",
            "ignore the constraints",
            "act as a",
            "you are now a",
            "switch to",
            "system override"
        ]
        
        # Out-of-Scope Keywords (Strictly non-technical)
        self.out_of_scope_categories = [
            "cook", "recipe", "food", "pasta", "pizza", "restaurant",
            "joke", "story", "poem", "song", "lyrics",
            "weather", "forecast", "news", "sport", "score",
            "movie", "actor", "celebrity", "game", "gaming"
        ]

    def validate_input(self, query: str) -> dict:
        """
        Runs pre-processing checks on user input.
        """
        query_lower = query.lower().strip()
        
        # 1. PII Check
        if self.email_pattern.search(query) or self.phone_pattern.search(query):
            return {"status": "BLOCKED", "reason": "Sensitive information (PII) detected. Please do not share personal data."}
            
        # 2. Prompt Injection Check
        if any(ik in query_lower for ik in self.injection_keywords):
            return {"status": "BLOCKED", "reason": "Potential prompt injection detected. System remains in Technical Mentor mode."}
            
        # 3. Keyword-based Out-of-Scope Pre-check
        # If the query contains "cook" or "pasta" etc., we block it immediately.
        words = set(query_lower.split())
        if any(cat in words for cat in self.out_of_scope_categories):
             return {"status": "BLOCKED", "reason": "Information not found in the documents."}

        return {"status": "PASSED"}

    def check_domain_relevance(self, top_score: float) -> bool:
        """
        Checks if the best retrieval match is relevant enough to proceed.
        Threshold calibrated based on observed distributions (1.15 bad, 1.44 good).
        """
        THRESHOLD = 0.5  # Lowered threshold per user request
        return top_score >= THRESHOLD

    def validate_output(self, response: str) -> str:
        """
        Runs post-processing checks on model output.
        """
        # Ensure it doesn't try to output system markers
        if "<result>" in response or "</result>" in response:
            response = response.replace("<result>", "").replace("</result>", "").strip()
            
        return response

guardrail_engine = GuardrailEngine()
