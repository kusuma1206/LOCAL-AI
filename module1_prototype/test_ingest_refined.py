import requests
import os
import time
from config import settings

def test_ingest_workflow():
    url = f"{settings.API_BASE_URL}/ingest-document"
    
    # Create a dummy test file
    test_file_path = "test_ingest_refined.md"
    content = """# Test Document for Refined Workflow
This is a sample document to verify the 9-step ingestion workflow.
It includes headings and content for the structure analyzer.

## Step 1: Uploading
The API should initialize the status to 'uploading'.

## Step 2: OneDrive
The file should be uploaded to OneDrive with a doc_id prefix.

## Step 3: Processing
The status should update to 'processing' before triggering the pipeline.
"""
    
    with open(test_file_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    print(f"--- Testing Refined Ingestion API ---")
    print(f"Uploading: {test_file_path}")
    
    try:
        with open(test_file_path, "rb") as f:
            files = {"file": (test_file_path, f, "text/markdown")}
            response = requests.post(url, files=files)
            
        if response.status_code == 200:
            result = response.json()
            print("\nSUCCESS: API accepted document!")
            print(f"Document ID: {result.get('document_id')}")
            print(f"OneDrive URL: {result.get('onedrive_url')}")
            
            doc_id = result.get('document_id')
            
            # The pipeline is currently synchronous, so it should already be 'ready'
            print(f"\nVerifying final status for doc_id {doc_id}...")
            
            from supabase import create_client
            from dotenv import load_dotenv
            load_dotenv()
            
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")
            supabase = create_client(supabase_url, supabase_key)
            
            res = supabase.table("documents").select("status", "storage_url").eq("doc_id", doc_id).execute()
            
            if res.data:
                final_status = res.data[0].get("status")
                storage_url = res.data[0].get("storage_url")
                print(f"Final Status: {final_status}")
                print(f"Storage URL: {storage_url}")
                
                if final_status == 'ready' and storage_url:
                    print("\nSUCCESS: Document reached 'ready' status with storage URL!")
                else:
                    print(f"\nWARNING: Document status is '{final_status}'. Expected 'ready'.")
            else:
                print("\nFAILURE: Could not find document in database.")
            
        else:
            print(f"\nFAILURE: {response.status_code} - {response.text}")
            if "status" in response.text and "uploading" in response.text:
                print("\nSuggestion: Ensure you have run 'add_status_and_url.sql' in Supabase to add missing columns.")

    except Exception as e:
        print(f"\nERROR: {e}")
    finally:
        if os.path.exists(test_file_path):
            os.remove(test_file_path)

if __name__ == "__main__":
    test_ingest_workflow()
