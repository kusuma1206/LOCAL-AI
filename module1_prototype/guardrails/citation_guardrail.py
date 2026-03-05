import re

class CitationGuardrail:
    """
    Guardrail to ensure LLM responses include proper citation metadata.
    """
    def __init__(self):
        # Patterns to look for in the response (e.g., [doc: 123, sec: 456] or similar structured format)
        self.doc_id_pattern = re.compile(r'document_id[:\s]+([a-zA-Z0-9_-]+)', re.IGNORECASE)
        self.section_id_pattern = re.compile(r'section_id[:\s]+([a-zA-Z0-9_-]+)', re.IGNORECASE)
        self.rejection_message = "The response is not properly grounded in retrieved source documents (missing citations)."

    def validate_citations(self, response: str) -> tuple[bool, str]:
        """
        Checks if the response contains references to document_id and section_id.
        
        Args:
            response (str): The LLM generated response.
            
        Returns:
            tuple[bool, str]: (True, "Success") if citations are present, (False, error_message) otherwise.
        """
        if not response:
            return False, "Empty response."

        has_doc_id = bool(self.doc_id_pattern.search(response))
        has_section_id = bool(self.section_id_pattern.search(response))

        if not (has_doc_id and has_section_id):
            print(f"CitationGuardrail: Validation failed. DocID: {has_doc_id}, SectionID: {has_section_id}")
            return False, self.rejection_message

        return True, "Citations found."
