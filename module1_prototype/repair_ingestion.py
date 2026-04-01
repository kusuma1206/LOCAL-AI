import os
import sys
import argparse
from dotenv import load_dotenv
from pathlib import Path

# Add project root to path
sys.path.append(os.getcwd())

from processing.storage import supabase, update_document_status
from main import run_ingestion_pipeline

def repair_broken_ingestions(dry_run=False):
    """
    Identifies documents stuck in 'processing' or 'uploading' status
    with NULL summaries and attempts to re-run the pipeline.
    """
    print("--- 🛠️ Ingestion Repair Utility ---")
    
    # 1. Fetch documents stuck with NULL summary/embedding
    res = supabase.table("documents").select("doc_id, title, filename, status, storage_url").or_("document_summary.is.null,document_embedding.is.null").execute()
    
    if not res.data:
        print("✅ No broken document records found (none have NULL summaries/embeddings).")
        return

    print(f"🔍 Found {len(res.data)} documents requiring repair.")
    
    UPLOAD_DIR = "uploads"
    INPUT_DIR = "input_docs"
    
    for doc in res.data:
        doc_id = doc["doc_id"]
        filename = doc["filename"]
        title = doc["title"]
        storage_url = doc["storage_url"]
        
        print(f"\nProcessing Doc ID: {doc_id} ('{filename}')...")
        
        # Determine the best file path to use
        # 1. Check uploads/
        file_path = os.path.join(UPLOAD_DIR, filename)
        if not os.path.exists(file_path):
            # 2. Check input_docs/
            file_path = os.path.join(INPUT_DIR, filename)
            
        if not os.path.exists(file_path):
            print(f"  [!] Skip: Source file '{filename}' not found locally in /uploads or /input_docs.")
            continue
            
        if dry_run:
            print(f"  [Dry Run] Would re-run ingestion for: {file_path}")
            continue

        print(f"  🚀 Restarting ingestion pipeline for {file_path}...")
        try:
            # We use doc_id_override to ensure we update the SAME record instead of creating a new one
            run_ingestion_pipeline(
                file_path, 
                title=title, 
                sharepoint_url=storage_url, 
                doc_id_override=doc_id
            )
            print(f"  ✅ Successfully repaired Doc {doc_id}.")
        except Exception as e:
            print(f"  ❌ Failed to repair Doc {doc_id}: {e}")
            update_document_status(doc_id, "error")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Repair broken or incomplete document ingestions.")
    parser.add_argument("--dry-run", action="store_true", help="Scan only without running ingestion")
    args = parser.parse_args()
    
    repair_broken_ingestions(dry_run=args.dry_run)
