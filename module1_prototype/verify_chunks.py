from processing.storage import supabase
import json

def verify_chunks():
    # Get latest document
    docs = supabase.table("documents").select("doc_id, title").order("doc_id", desc=True).limit(1).execute()
    if not docs.data:
        print("No documents found.")
        return
    
    doc = docs.data[0]
    print(f"Checking Document {doc['doc_id']}: {doc['title']}")
    
    # Get sections
    sections = supabase.table("sections").select("section_id, title").eq("document_id", doc['doc_id']).execute()
    print(f"Found {len(sections.data)} sections.")
    
    total_chunks = 0
    for s in sections.data:
        chunks = supabase.table("document_chunks").select("chunk_id").eq("section_id", s['section_id']).execute()
        count = len(chunks.data)
        print(f" - Section '{s['title']}': {count} chunks")
        total_chunks += count
        
    print(f"\nTotal Chunks for document: {total_chunks}")
    if total_chunks > 0:
        print("✅ VERIFICATION SUCCESS: Chunks are populating!")
    else:
        print("❌ VERIFICATION FAILURE: No chunks found.")

if __name__ == "__main__":
    verify_chunks()
