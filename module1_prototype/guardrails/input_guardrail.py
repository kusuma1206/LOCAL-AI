class InputGuardrail:
    """
    Guardrail for sanitizing and validating user input queries.
    """
    def __init__(self):
        self.min_length = 5
        self.banned_phrases = ["hack", "jailbreak", "ignore instructions"]

    def validate_query(self, query: str) -> tuple[bool, str]:
        """
        Validates the user query for basic safety and formatting.
        
        Args:
            query (str): The user's input query.
            
        Returns:
            tuple[bool, str]: (True, message) if valid, (False, error_message) otherwise.
        """
        # 1. Check if query is empty or just whitespace
        if not query or not query.strip():
            return False, "Query cannot be empty."

        # 2. Check query length
        if len(query.strip()) <= self.min_length:
            return False, f"Query is too short. Minimum length is {self.min_length} characters."

        # 3. Check for banned phrases (case-insensitive)
        query_lower = query.lower()
        for phrase in self.banned_phrases:
            if phrase in query_lower:
                return False, f"Query contains restricted content: '{phrase}'."

        return True, "Query passed validation."

    def sanitize(self, query: str) -> str:
        """
        Sanitizes the user query by removing potentially harmful characters or patterns.
        """
        # Placeholder for future expansion
        return query.strip()
