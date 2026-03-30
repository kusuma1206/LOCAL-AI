from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def diagnose():
    try:
        print("--- Documents Check ---")
        docs = supabase.table("documents").select("doc_id, title, document_summary, document_embedding").execute()
        if docs.data:
            for d in docs.data:
                emb_status = "Populated" if d.get('document_embedding') else "MISSING"
                sum_status = "Populated" if d.get('document_summary') else "MISSING"
                print(f"ID: {d['doc_id']} | Title: {d['title']} | Summary: {sum_status} | Embedding: {emb_status}")
        else:
            print("No documents found.")

        print("\n--- Sections Check ---")
        secs = supabase.table("sections").select("section_id, title, section_summary, section_embedding").limit(5).execute()
        if secs.data:
            for s in secs.data:
                emb_status = "Populated" if s.get('section_embedding') else "MISSING"
                sum_status = "Populated" if s.get('section_summary') else "MISSING"
                print(f"ID: {s['section_id']} | Title: {s['title']} | Summary: {sum_status} | Embedding: {emb_status}")
        else:
            print("No sections found.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    diagnose()
