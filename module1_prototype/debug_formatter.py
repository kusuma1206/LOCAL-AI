
from retrieval import response_formatter

sample_text = """
### 1.1 High-Level Architecture
The system is designed as a Python-based backend service that interacts with Supabase for data persistence.
graph TD
  A[User] --> B[FastAPI]
  B --> C[Supabase]

#### ≡ƒæñ POST /user/register
Registers a new user with details such as name, email, password, and phone number.
"""

print("--- Testing clean_markdown_noise ---")
cleaned = response_formatter.clean_markdown_noise(sample_text)
print(f"Cleaned output:\n'{cleaned}'")

print("\n--- Testing format_conversational_response ---")
sections = [
    {
        "document_name": "TestDoc",
        "document_id": "DOC_12345",
        "section_name": "Architecture",
        "content_text": sample_text,
        "similarity_score": 0.9
    }
]
response = response_formatter.format_conversational_response("architecture", sections)
print(f"Final Response:\n{response}")
