import json
from config import settings
from processing import storage
from retrieval import chunk_retriever, query_embedder, section_retriever

def test():
    query = "Explain Sakhi WhatsApp backend overview in detail"
    print(f"Query: {query}")
        
    query_embedding = query_embedder.embed_query(query)
    
    top_sections = section_retriever.retrieve_top_sections(storage.supabase, query_embedding, top_n=5)
    section_ids = [s["section_id"] for s in top_sections]
    print(f"Top Sections: {section_ids}")

    chunks = chunk_retriever.retrieve_top_chunks(storage.supabase, query_embedding, section_ids, top_k=12)
    
    print("\n--- Retrieved Chunks ---")
    for i, c in enumerate(chunks):
        content = c.get('content', '')
        words = len(content.split())
        print(f"\nChunk {i+1} (Section {c.get('section_id')}) - {words} words:")
        print("-" * 20)
        print(content[:200] + "..." if len(content) > 200 else content)
        print("-" * 20)

if __name__ == "__main__":
    test()
