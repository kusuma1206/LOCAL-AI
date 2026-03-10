from processing.storage import supabase
import numpy as np

def test_rpc():
    print("Testing match_sections RPC...")
    
    # Generate a dummy embedding (zeros)
    query_embedding = [0.0] * 384
    
    try:
        # Call the RPC
        response = supabase.rpc("match_sections", {
            "query_embedding": query_embedding,
            "match_count": 5,
            "document_ids": None
        }).execute()
        
        print(f"RPC Response: {len(response.data)} sections found.")
        section_ids = []
        if response.data:
            for i, row in enumerate(response.data):
                print(f"  [{i}] ID: {row['id']} | Title: {row['section_title']} | Similarity: {row['similarity']}")
                section_ids.append(row['id'])
        else:
            print("No sections found. Check if EXISTS clause is preventing retrieval.")
            return

        # 2. Test match_chunks
        print("\nTesting match_chunks RPC...")
        chunk_response = supabase.rpc("match_chunks", {
            "query_embedding": query_embedding,
            "match_count": 5,
            "section_ids": section_ids
        }).execute()
        
        print(f"Chunk RPC Response: {len(chunk_response.data)} chunks found.")
        if chunk_response.data:
            for i, row in enumerate(chunk_response.data):
                print(f"  [{i}] Section ID: {row['section_id']} | Content Snippet: {row['content'][:50]}... | Similarity: {row['similarity']}")
        else:
            print("No chunks found for these sections.")
            
    except Exception as e:
        print(f"RPC Error: {e}")

if __name__ == "__main__":
    test_rpc()
