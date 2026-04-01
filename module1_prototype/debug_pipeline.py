import os
import sys
import argparse
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.getcwd())

from main import run_ingestion_pipeline
from processing.storage import supabase

def debug_file(file_path, doc_id=None):
    print(f"--- 🔍 Debugging Ingestion for: {file_path} ---")
    
    if not os.path.exists(file_path):
        print(f"❌ Error: File not found at {file_path}")
        return

    # If doc_id is not provided, try to find it by filename
    if not doc_id:
        filename = os.path.basename(file_path)
        res = supabase.table("documents").select("doc_id").eq("filename", filename).execute()
        if res.data:
            doc_id = res.data[0]["doc_id"]
            print(f"ℹ️ Found existing doc_id: {doc_id}")
        else:
            print("ℹ️ No existing record found. Pipeline will create a new one.")

    print(f"🚀 Running pipeline...")
    try:
        run_ingestion_pipeline(
            file_path, 
            doc_id_override=doc_id
        )
        print("\n✅ Debug Run Complete.")
        
        # Verify final state
        if doc_id:
            verify = supabase.table("documents").select("doc_id, status, document_summary, document_embedding").eq("doc_id", doc_id).execute()
            if verify.data:
                d = verify.data[0]
                print(f"\nFinal State for Doc {doc_id}:")
                print(f"  Status: {d['status']}")
                print(f"  Summary length: {len(d['document_summary']) if d['document_summary'] else 'NULL'}")
                print(f"  Embedding length: {len(d['document_embedding']) if d['document_embedding'] else 'NULL'}")
    except Exception as e:
        print(f"\n❌ Pipeline Crashed: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Synchronously debug the ingestion pipeline.")
    parser.add_argument("file_path", help="Path to the document to process")
    parser.add_argument("--id", type=int, help="Optional document ID to update")
    args = parser.parse_args()
    
    debug_file(args.file_path, doc_id=args.id)
