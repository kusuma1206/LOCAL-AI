from retrieval.response_formatter import format_doc_response, format_multiple_results
import os

def test_sakhi_whatsapp_backend():
    query = "How does Sakhi route chat interactions?"
    doc_name = "system_design.md"
    
    # Raw data fragments from user input
    sections = [
        {
            "section_name": "Overview",
            "document_name": doc_name,
            "page_number": 1,
            "similarity_score": 0.82,
            "content_text": "main.py is the core FastAPI application that orchestrates the entire Sakhi chatbot system. It handles user registration, onboarding, and most importantly, the intelligent chat routing between different AI models based on query complexity."
        },
        {
            "section_name": "1. High-Level Architecture",
            "document_name": doc_name,
            "page_number": 1,
            "similarity_score": 0.88,
            "content_text": "The system is designed as a Python-based backend service that interacts with Supabase for data persistence and vector search, and OpenAI for intelligence (LLM and Embeddings). It serves as the brain for a WhatsApp chatbot."
        },
        {
            "section_name": "Key Components",
            "document_name": doc_name,
            "page_number": 2,
            "similarity_score": 0.96,
            "content_text": """#### 💬 `POST /sakhi/chat` ⭐ **MAIN ENDPOINT**
- Handles all chat interactions
- Implements **3-stage onboarding flow**
- Routes to appropriate AI model based on complexity
- **Returns:** Reply, mode, language, YouTube links, infographics"""
        },
        {
            "section_name": "Key Components",
            "document_name": doc_name,
            "page_number": 2,
            "similarity_score": 0.91,
            "content_text": """### 1. **Endpoints** (The API Surface)
- Health check endpoint
- Returns: `{"message": "Sakhi API working!"}`"""
        },
        {
            "section_name": "4. Key Data Flows",
            "document_name": doc_name,
            "page_number": 4,
            "similarity_score": 0.94,
            "content_text": "### 4.2 RAG (Retrieval-Augmented Generation) Response\n1. Query: User asks a medical question. 2. Embedding: rag_search.py generates an embedding. 3. Search: FAQ Match, KB Match, Hierarchical Match."
        }
    ]

    # Test 1: Multiple Results with Merging
    print("Generating multiple results summary...")
    multi_output = format_multiple_results(sections)
    
    # Test 2: Single Detailed Response (using the highest similarity merged section)
    # Note: format_doc_response is usually called on one section, 
    # but here we'll use the "Key Components" section which had two fragments.
    # In a real app, merging happens before formatting.
    
    # Find fragments for 'Key Components'
    key_comp_fragments = [s["content_text"] for s in sections if s["section_name"] == "Key Components"]
    merged_content = "\n\n".join(key_comp_fragments)
    
    print("Generating single detailed response...")
    single_output = format_doc_response(
        query=query,
        document_name=doc_name,
        page_number=2,
        section_name="Key Components",
        content_text=merged_content,
        similarity_score=0.96
    )

    # Save outputs
    output_file = "sakhi_final_test.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("="*20 + " MULTIPLE RESULTS " + "="*20 + "\n\n")
        f.write(multi_output)
        f.write("\n\n" + "="*20 + " SINGLE DETAILED VIEW " + "="*20 + "\n\n")
        f.write(single_output)

    print(f"Test complete. Output written to {output_file}")

if __name__ == "__main__":
    test_sakhi_whatsapp_backend()
