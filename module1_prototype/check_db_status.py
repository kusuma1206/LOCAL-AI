from processing.storage import supabase
import json

def check_db():
    print("Checking database population...")
    
    # Check documents
    docs = supabase.table("documents").select("doc_id, title, status").order("doc_id", desc=True).limit(5).execute()
    print(f"\nRecent Documents:\n{json.dumps(docs.data, indent=2)}")
    
    if docs.data:
        latest_id = docs.data[0]["doc_id"]
        
        # Check sections
        sections = supabase.table("sections").select("section_id, title, parent_section_id, level").eq("document_id", latest_id).execute()
        print(f"\nSections for doc {latest_id}: {len(sections.data)}")
        for s in sections.data:
            parent = s['parent_section_id'] if s['parent_section_id'] else "None"
            print(f" - [{s['level']}] {s['title']} (Parent: {parent})")
            
        if sections.data:
            latest_section_id = sections.data[0]["section_id"]
            # Check chunks
            chunks = supabase.table("document_chunks").select("chunk_id").eq("section_id", latest_section_id).execute()
            print(f"\nChunks for section {latest_section_id}: {len(chunks.data)}")
    
if __name__ == "__main__":
    check_db()
