from processing.storage import supabase
import uuid

def test_insertion():
    print("Testing insertion into document_chunks...")
    
    # Use a dummy section ID or find an existing one
    try:
        sec_res = supabase.table("sections").select("id").limit(1).execute()
        if not sec_res.data:
            print("No sections found to link to. Creating a dummy section...")
            # This might also fail due to RLS
            dummy_doc_id = str(uuid.uuid4())
            sec_data = {
                "document_id": dummy_doc_id,
                "section_title": "Test Section",
                "section_summary": "Test Summary",
                "section_embedding": [0.1] * 384
            }
            sec_res = supabase.table("sections").insert(sec_data).execute()
            section_id = sec_res.data[0]["id"]
        else:
            section_id = sec_res.data[0]["id"]
            
        print(f"Using section_id: {section_id}")
        
        chunk_data = {
            "section_id": section_id,
            "content": "This is a test chunk insertion.",
            "embedding": [0.1] * 384,
            "chunk_hash": "test_hash_" + str(uuid.uuid4())
        }
        
        res = supabase.table("document_chunks").insert(chunk_data).execute()
        print("Success! Data inserted:", res.data)
        
    except Exception as e:
        print(f"\n!!! INSERTION FAILED !!!")
        print(f"Error type: {type(e)}")
        print(f"Error message: {e}")

if __name__ == "__main__":
    test_insertion()
