import os
import sys
from supabase import create_client

# Add project root to path
sys.path.append(os.getcwd())
from retrieval import mode_router, chunk_retriever
from processing import storage

def verify_hierarchical_retrieval():
    print("\n--- VERIFYING HIERARCHICAL RETRIEVAL ---")
    query = "What are the four layers of zero trust AI architecture?"
    
    # 1. Test Retriever Directly
    model = None # embedder handles this
    query_embedding = None 
    
    # We need to get the embedding first
    from processing import embedder
    model = embedder.get_model()
    query_embedding = model.encode([query])[0].tolist()
    
    # Get sections first (Level 1)
    res_docs = storage.supabase.rpc("match_documents", {"query_embedding": query_embedding, "match_count": 1}).execute()
    if not res_docs.data:
        print("❌ No documents found.")
        return
    
    doc_id = res_docs.data[0]["doc_id"]
    res_sections = storage.supabase.rpc("match_sections", {"query_embedding": query_embedding, "match_count": 3, "document_ids": [doc_id]}).execute()
    
    section_ids = [s["id"] for s in res_sections.data]
    print(f"Matched Sections: {[s['section_title'] for s in res_sections.data]}")
    
    # Get Chunks (Level 2) with Expansion
    top_chunks = chunk_retriever.retrieve_top_chunks(storage.supabase, query_embedding, section_ids)
    
    print(f"\nRetrieved {len(top_chunks)} logical units.")
    for i, c in enumerate(top_chunks):
        content = c["content"]
        word_count = len(content.split())
        print(f"\nUnit {i+1} (Words: {word_count}):")
        print(f"Content Start: {content[:200]}...")
        
    # Check if "Layer 1: Similarity Gate" is in there
    if any("Similarity Gate" in c["content"] for c in top_chunks):
        print("\n[OK] Success: Heading-aware expansion pulled section content.")
    else:
        print("\n[ERROR] Failure: Only heading or incomplete content retrieved.")

    # 3. Test Full Formatter Output
    results = mode_router.handle_query(storage.supabase, query, "explain")
    final_response = results.get("formatted_answer", "NO ANSWER GENERATED")
    
    with open("retrieval_result.md", "w", encoding="utf-8") as f:
        f.write(final_response)
    
    print("\n--- RESULTS WRITTEN TO retrieval_result.md ---")

if __name__ == "__main__":
    verify_hierarchical_retrieval()
