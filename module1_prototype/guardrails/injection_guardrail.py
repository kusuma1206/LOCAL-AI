class InjectionGuardrail:
    """
    Guardrail for detecting and preventing prompt injection attempts.
    """
    def __init__(self):
        # List of blocked patterns that indicate a potential prompt injection attack
        self.blocked_patterns = [
            "ignore previous instructions",
            "reveal system prompt",
            "developer message",
            "act as",
            "jailbreak"
        ]

    def detect_injection(self, query: str) -> bool:
        """
        Analyzes the query for potential prompt injection patterns.
        
        Args:
            query (str): The user's input query.
            
        Returns:
            bool: True if the query is safe, False if prompt injection is detected.
        """
        if not query:
            return True

        query_lower = query.lower()
        
        for pattern in self.blocked_patterns:
            if pattern in query_lower:
                print(f"Injection detected: Found blocked pattern '{pattern}'")
                return False
                
        return True
