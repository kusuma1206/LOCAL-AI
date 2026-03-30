import requests
import os
import time
from config import settings

API_URL = settings.API_BASE_URL
TEST_FILE = "large_ingestion_test.md"

# 1. Create a sufficiently large test file
with open(TEST_FILE, "w") as f:
    f.write("# Technical Specification\n\n" + "This is a detailed technical sentence used for validating the hierarchical ingestion pipeline. " * 5)

def test_reingestion_flow():
    print("--- Starting Re-ingestion Verification ---")
    
    import hashlib
    with open(TEST_FILE, "rb") as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()

    # 1. Check existence (should be false)
    print(f"\n1. Checking existence of {TEST_FILE}...")
    res = requests.post(f"{API_URL}/documents/check", json={"file_name": TEST_FILE, "file_hash": file_hash})
    print(f"   Status: {res.status_code}")
    try:
        data = res.json()
        print(f"   Result: {data}")
    except:
        print(f"   Response text: {res.text}")
        data = {}
    
    # 2. Upload first time
    print("\n2. Uploading first time...")
    with open(TEST_FILE, "rb") as f:
        res = requests.post(
            f"{API_URL}/ingest-document",
            files={"file": (TEST_FILE, f)},
            data={"document_title": "Test Doc", "uploaded_by": "Verifier", "replace": "false"}
        )
    try:
        data = res.json()
        doc_id = data.get("document_id")
        if doc_id:
            print(f"   Success. Document ID: {doc_id}")
        else:
            print(f"   Upload returned no doc_id: {data}")
            # If doc exists already, this might fail due to unique constraint. 
            # Let's check existence again.
    except:
        print(f"   Upload failed: {res.text}")
        return
    
    # 3. Check existence again (should be true and hash_match true)
    print("\n3. Checking existence again (with hash)...")
    res = requests.post(f"{API_URL}/documents/check", json={"file_name": TEST_FILE, "file_hash": file_hash})
    try:
        existence_data = res.json()
        print(f"   Result: {existence_data}")
    except:
        print(f"   Check failed: {res.text}")
        return
    
    if existence_data.get("exists"):
        # 5. Perform replacement
        print("\n5. Performing replacement (replace=true)...")
        with open(TEST_FILE, "rb") as f:
            res = requests.post(
                f"{API_URL}/ingest-document",
                files={"file": (TEST_FILE, f)},
                data={"document_title": "Replacer Doc", "uploaded_by": "Verifier", "replace": "true"}
            )
        print(f"   Result: {res.json()}")
    # --- 1. Initial Upload ---
    print("\n--- 1. Initial Upload ---")
    file_path = "uploads/large_test.md"
    file_name = "large_test.md"
    print("\n--- Verification Complete ---")

if __name__ == "__main__":
    try:
        test_reingestion_flow()
    finally:
        if os.path.exists(TEST_FILE):
            os.remove(TEST_FILE)
