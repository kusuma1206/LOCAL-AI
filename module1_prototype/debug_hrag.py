from retrieval import query_embedder, document_retriever, section_retriever, chunk_retriever
from processing.storage import supabase
import json

def debug_hierarchical_retrieval():
    query = "What is zero trust ai architecture"
    print(f"DEBUG: Query: {query}")
    
    # 1. Embed
    embed = query_embedder.embed_query(query)
    print(f"DEBUG: Embedding generated. Dim: {len(embed)}")
    
    # 2. Documents
    docs = document_retriever.retrieve_top_documents(supabase, embed, top_k=3)
    print(f"DEBUG: Top Docs Found: {[d['doc_id'] for d in docs]}")
    for d in docs:
        print(f"  - ID: {d['doc_id']} | Filename: {d['filename']} | Score: {d['similarity_score']}")
        
    if not docs:
        return
        
    doc_ids = [d["doc_id"] for d in docs]
    
    # 3. Sections
    print("\n--- Testing Sections with Filter ---")
    secs = section_retriever.retrieve_top_sections(supabase, embed, top_n=5, doc_ids=doc_ids)
    print(f"DEBUG: Top Sections Found: {len(secs)}")
    
    print("\n--- Testing Sections WITHOUT Filter ---")
    secs_no_filter = section_retriever.retrieve_top_sections(supabase, embed, top_n=5, doc_ids=None)
    print(f"DEBUG: Top Sections (No Filter) Found: {len(secs_no_filter)}")
    for s in secs_no_filter:
        print(f"  - ID: {s['section_id']} | DocID: {s.get('doc_id')} | Title: {s['section_title']} | Score: {s['similarity_score']}")
        
    if not secs:
        # Check if ANY sections exist for these doc_ids
        raw_secs = supabase.table("sections").select("id, doc_id, section_title").in_("doc_id", doc_ids).execute()
        print(f"DEBUG: Raw Sections in DB for these doc_ids: {len(raw_secs.data)}")
        return
        
    sec_ids = [s["section_id"] for s in secs]
    
    # 4. Chunks
    chunks = chunk_retriever.retrieve_top_chunks(supabase, embed, sec_ids, top_k=5)
    print(f"DEBUG: Top Chunks Found: {len(chunks)}")

if __name__ == "__main__":
    debug_hierarchical_retrieval()
