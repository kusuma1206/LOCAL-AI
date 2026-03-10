from processing.storage import supabase

def check_counts():
    try:
        docs_res = supabase.table("documents").select("id").execute()
        print(f"Documents: {len(docs_res.data)}")
        
        secs_res = supabase.table("sections").select("id").execute()
        print(f"Sections: {len(secs_res.data)}")
        
        chunks_res = supabase.table("document_chunks").select("id").execute()
        print(f"Chunks (nollm): {len(chunks_res.data)}")
        
        # Also check the old table just in case
        old_chunks_res = supabase.table("document_chunks").select("id").execute()
        print(f"Chunks (old): {len(old_chunks_res.data)}")
        
    except Exception as e:
        print(f"Error checking counts: {e}")

if __name__ == "__main__":
    check_counts()
