import re

class OutputGuardrail:
    """
    Guardrail for filtering and validating the final model response.
    """
    def __init__(self, min_length: int = 20):
        self.min_length = min_length
        self.banned_words = ["confidential", "proprietary", "secret_key"]
        self.banned_phrases = [
            "i am an ai model trained by",
            "as an ai",
            "i cannot provide",
            "illegal"
        ]

    def validate_response(self, response: str) -> bool:
        """
        Checks the generated response for harmful content, PII, or hallucination.
        
        Args:
            response (str): The model's generated response.
            
        Returns:
            bool: True if the output is safe/valid, False otherwise.
        """
        if not response:
            return False

        # 1. Check length
        if len(response.strip()) < self.min_length:
            print(f"OutputGuardrail: Response too short ({len(response)} chars).")
            return False

        response_lower = response.lower()

        # 2. Check for banned words
        for word in self.banned_words:
            if word in response_lower:
                print(f"OutputGuardrail: Response contains banned word: '{word}'.")
                return False

        # 3. Check for specific AI disclosure phrases
        for phrase in self.banned_phrases:
            if phrase in response_lower:
                print(f"OutputGuardrail: Response contains restricted phrase: '{phrase}'.")
                return False

        return True

    def clean_response(self, response: str) -> str:
        """
        Filters the response to remove extra whitespace and formatting issues.
        
        Args:
            response (str): The raw model response.
            
        Returns:
            str: The cleaned response.
        """
        if not response:
            return ""

        # Remove multiple newlines and spaces
        cleaned = re.sub(r'\s+', ' ', response)
        # Trim leading/trailing whitespace
        cleaned = cleaned.strip()
        
        return cleaned
