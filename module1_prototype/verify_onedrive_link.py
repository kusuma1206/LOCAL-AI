import requests
import time
import os
from config import settings

API_URL = settings.API_BASE_URL

def verify_onedrive_link():
    print("--- Starting OneDrive Link Verification ---")
    
    # 1. Ingest a document
    test_file = "large_ingestion_test.md"
    # Create the file if it doesn't exist (re-use the one from previous steps)
    if not os.path.exists(test_file):
        with open(test_file, "w") as f:
            f.write("# Verification Document\n\nThis is a test document for OneDrive link verification.\n" + "Word " * 100)

    print(f"Ingesting {test_file}...")
    with open(test_file, "rb") as f:
        files = {"file": (test_file, f)}
        data = {
            "document_title": "OneDrive Link Test Doc",
            "uploaded_by": "Verification Script",
            "replace": "true"
        }
        res = requests.post(f"{API_URL}/ingest-document", files=files, data=data)
    
    if res.status_code != 200:
        print(f"Failed to ingest: {res.text}")
        return
    
    ingest_data = res.json()
    doc_id = ingest_data.get("document_id")
    onedrive_url = ingest_data.get("onedrive_url")
    print(f"Ingestion successful. Doc ID: {doc_id}, URL: {onedrive_url}")
    
    # 2. Wait for background processing
    print("Waiting for processing (10s)...")
    time.sleep(10)
    
    # 3. Verify in Database
    print("Checking database directly...")
    from processing.storage import supabase
    db_res = supabase.table("documents").select("storage_url").eq("doc_id", doc_id).execute()
    if db_res.data and db_res.data[0].get("storage_url"):
        stored_url = db_res.data[0]["storage_url"]
        print(f"Success: URL stored in DB: {stored_url}")
    else:
        print("Failure: URL NOT stored in DB!")
        return

    # 4. Perform a query and check the response
    print("Performing chat query...")
    query_payload = {
        "query": "Tell me about the verification document",
        "mode": "technical",
        "history": []
    }
    chat_res = requests.post(f"{API_URL}/chat", json=query_payload)
    
    if chat_res.status_code == 200:
        chat_data = chat_res.json()
        formatted_answer = chat_data.get("result", {}).get("formatted_answer", "")
        print("Chat Response:")
        print("-" * 20)
        print(formatted_answer)
        print("-" * 20)
        
        if "[View Original Document]" in formatted_answer and stored_url in formatted_answer:
            print("Success: Professional link found in chat response!")
        else:
            print("Failure: Professional link NOT found in chat response!")
    else:
        print(f"Chat failed: {chat_res.text}")

if __name__ == "__main__":
    verify_onedrive_link()
