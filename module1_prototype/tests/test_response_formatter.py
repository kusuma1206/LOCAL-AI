import sys
import os

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from retrieval.response_formatter import format_doc_response, format_multiple_results

def test_formatter():
    query = "How does WhatsApp route messages?"
    document_name = "WhatsApp Architecture.pdf"
    page_number = 14
    section_name = "Backend Architecture"
    content_text = """WhatsApp uses distributed Erlang servers to handle millions of users.

### Key Components

• Load Balancer
- Message Queue
* Routing Server

Message routing is handled through distributed queue systems. These work together for high availability."""
    similarity_score = 0.87
    
    result = format_doc_response(query, document_name, page_number, section_name, content_text, similarity_score)
    
    # Test multiple results with merging
    sections = [
        {
            "section_name": "API Layer",
            "document_name": "API_DOC.md",
            "page_number": 1,
            "similarity_score": 0.95,
            "content_text": "The API layer handles all incoming requests from the frontend using FastAPI."
        },
        {
            "section_name": "API Layer",
            "document_name": "API_DOC.md",
            "page_number": 1,
            "similarity_score": 0.96,
            "content_text": "It ensures secure transmission of data between modules."
        }
    ]
    multi_result = format_multiple_results(sections)
    
    with open("test_output.txt", "w", encoding="utf-8") as f:
        f.write("--- SINGLE RESULT (Intelligent Assistant) ---\n")
        f.write(result)
        f.write("\n\n--- MULTIPLE RESULTS ---\n")
        f.write(multi_result)
    
    print("Formatted output written to test_output.txt")

if __name__ == "__main__":
    test_formatter()
