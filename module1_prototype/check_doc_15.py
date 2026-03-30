from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def check_doc(doc_id):
    try:
        res = supabase.table("documents").select("*").eq("doc_id", doc_id).execute()
        if res.data:
            doc = res.data[0]
            print(f"Doc ID: {doc['doc_id']}")
            print(f"Title: {doc['title']}")
            print(f"Summary Preview: {doc.get('document_summary', 'NULL')[:200]}...")
            emb = doc.get('document_embedding')
            print(f"Embedding Status: {'Populated' if emb else 'NULL'}")
            if emb:
                print(f"Embedding Sample: {emb[:5]} (Total {len(emb)})")
        else:
            print(f"Doc ID {doc_id} not found.")
            
        print("\n--- Sections Count ---")
        sec_res = supabase.table("sections").select("section_id").eq("document_id", doc_id).execute()
        print(f"Sections found: {len(sec_res.data) if sec_res.data else 0}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_doc(15)
