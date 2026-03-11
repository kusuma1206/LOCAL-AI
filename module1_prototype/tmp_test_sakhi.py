from retrieval.response_formatter import format_doc_response, format_multiple_results
import json

def test_sakhi_output():
    query = "How does Sakhi route chat interactions?"
    doc_name = "system_design.md"
    
    sections = [
        {
            "section_name": "Overview",
            "document_name": doc_name,
            "page_number": 1,
            "similarity_score": 0.85,
            "content_text": "main.py is the core FastAPI application that orchestrates the entire Sakhi chatbot system. It handles user registration, onboarding, and most importantly, the intelligent chat routing between different AI models based on query complexity."
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
- **Returns:** Reply, mode, language, YouTube links, infographics

#### 📝 `POST /user/answers`
- Saves bulk user questionnaire responses
- Used for collecting user health data"""
        },
        {
            "section_name": "Key Components",
            "document_name": doc_name,
            "page_number": 2,
            "similarity_score": 0.92,
            "content_text": """### 1. **Endpoints** (The API Surface)

- Health check endpoint
- Returns: `{"message": "Sakhi API working!"}`

#### 👤 `POST /user/register`
- Full user registration with name, email, password, phone
- Creates user profile in database
- **Returns:** `user_id` and user details"""
        },
        {
            "section_name": "1. High-Level Architecture",
            "document_name": doc_name,
            "page_number": 1,
            "similarity_score": 0.88,
            "content_text": "The system is designed as a Python-based backend service that interacts with Supabase for data persistence and vector search, and OpenAI for intelligence (LLM and Embeddings). It serves as the brain for a WhatsApp chatbot."
        },
        {
            "section_name": "4. Key Data Flows",
            "document_name": doc_name,
            "page_number": 4,
            "similarity_score": 0.94,
            "content_text": "### 4.2 RAG (Retrieval-Augmented Generation) Response\n1. Query: User asks a medical question. 2. Embedding: rag_search.py generates an embedding. 3. Search: FAQ Match, KB Match, Hierarchical Match."
        }
    ]

    # 1. Show Multiple Results (Merged)
    multi_output = format_multiple_results(sections)
    
    # 2. Show Single Detailed Result (Best Match)
    # We take the best match for the demo
    best_sec = sections[1] # Key Components has the POST /sakhi/chat info
    single_output = format_doc_response(
        query, 
        best_sec["document_name"], 
        best_sec["page_number"], 
        best_sec["section_name"], 
        # For single result we usually have the merged text if we want accurate demo, 
        # but here we just use the best fragment's content.
        # However, merge_sections is usually called before this in a real flow.
        best_sec["content_text"], 
        best_sec["similarity_score"]
    )

    with open("sakhi_preview.txt", "w", encoding="utf-8") as f:
        f.write("=== SINGLE DETAILED RESPONSE (Sakhi Chat Routing) ===\n\n")
        f.write(single_output)
        f.write("\n\n" + "="*50 + "\n\n")
        f.write("=== MULTIPLE RESULTS SUMMARY ===\n\n")
        f.write(multi_output)

    print("Sakhi preview written to sakhi_preview.txt")

if __name__ == "__main__":
    test_sakhi_output()
