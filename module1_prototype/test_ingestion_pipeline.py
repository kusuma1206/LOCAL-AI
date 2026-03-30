import os
import time
import requests
from dotenv import load_dotenv
from config import settings
from processing.sharepoint import get_onedrive_access_token, upload_to_onedrive, download_from_onedrive
from processing.storage import supabase, create_document, update_document_status, insert_section, insert_document_chunk
from processing import extractor, structure_analyzer, chunker, embedder

def run_diagnostic():
    load_dotenv()
    summary = {}
    
    print("\n" + "="*60)
    print("      RAG INGESTION PIPELINE DIAGNOSTIC SYSTEM")
    print("="*60 + "\n")

    # --- STEP 1: Environment Validation ---
    print("STEP 1 — Environment Validation")
    env_vars = [
        "ONEDRIVE_CLIENT_ID", "ONEDRIVE_TENANT_ID", "ONEDRIVE_USER_ID", 
        "ONEDRIVE_FOLDER_NAME", "SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"
    ]
    all_env_ok = True
    for var in env_vars:
        val = os.getenv(var)
        status = "LOADED" if val else "MISSING"
        print(f"  {var:<25}: {status}")
        if not val: all_env_ok = False
    
    summary["Environment"] = "OK" if all_env_ok else "FAILED"
    if not all_env_ok: return print_final_summary(summary)

    # --- STEP 2: Microsoft Graph Authentication ---
    print("\nSTEP 2 — Microsoft Graph Authentication")
    try:
        tenant_id = os.getenv("ONEDRIVE_TENANT_ID")
        client_id = os.getenv("ONEDRIVE_CLIENT_ID")
        client_secret = os.getenv("ONEDRIVE_CLIENT_SECRET")
        
        token = get_onedrive_access_token(tenant_id, client_id, client_secret)
        if token:
            print(f"  Access token obtained successfully.")
            print(f"  Token Prefix: {token[:20]}...")
            summary["Authentication"] = "OK"
        else:
            raise Exception("Token received was empty")
    except Exception as e:
        print(f"  [!] Auth Failed: {e}")
        summary["Authentication"] = "FAILED"
        return print_final_summary(summary)

    # --- STEP 3: OneDrive Upload Test ---
    print("\nSTEP 3 — OneDrive Upload Test")
    test_filename = "diagnostic_test.md"
    test_content = b"# Diagnostic Test\nThis file verifies the ingestion pipeline."
    temp_doc_id = 999
    
    try:
        up_res = upload_to_onedrive(test_content, test_filename, temp_doc_id)
        web_url = up_res.get("webUrl")
        item_id = up_res.get("id")
        print(f"  File uploaded successfully.")
        print(f"  OneDrive URL: {web_url}")
        print(f"  File ID: {item_id}")
        summary["Upload"] = "OK"
    except Exception as e:
        print(f"  [!] Upload Failed: {e}")
        summary["Upload"] = "FAILED"
        return print_final_summary(summary)

    # --- STEP 4: Database Insert Test ---
    print("\nSTEP 4 — Database Insert Test")
    try:
        doc_id = create_document("Diagnostic Test Doc", test_filename)
        if doc_id:
            print(f"  doc_id created: {doc_id}")
            summary["Database Insert"] = "OK"
        else:
            raise Exception("create_document returned None")
    except Exception as e:
        print(f"  [!] DB Insert Failed: {e}")
        summary["Database Insert"] = "FAILED"
        # continue but mark as failed

    # --- STEP 5: Update Document Metadata ---
    print("\nSTEP 5 — Update Document Metadata")
    try:
        update_document_status(doc_id, "processing", storage_url=web_url)
        print("  Metadata update successful (status='processing').")
        summary["Metadata Update"] = "OK"
    except Exception as e:
        print(f"  [!] Metadata Update Failed: {e}")
        summary["Metadata Update"] = "FAILED"

    # --- STEP 6: Download File From OneDrive ---
    print("\nSTEP 6 — Download File From OneDrive")
    try:
        downloaded_content = download_from_onedrive(item_id)
        print("  File downloaded successfully.")
        print(f"  File Size: {len(downloaded_content)} bytes")
        summary["Download"] = "OK"
    except Exception as e:
        print(f"  [!] Download Failed: {e}")
        summary["Download"] = "FAILED"

    # --- STEP 7: Text Extraction ---
    print("\nSTEP 7 — Text Extraction")
    # We'll use a local temp file for the extractor
    temp_local = "temp_diag.md"
    with open(temp_local, "wb") as f:
        f.write(downloaded_content)
    
    try:
        ext_res = extractor.extract_text(temp_local)
        text = ext_res["text"]
        print(f"  Characters extracted: {len(text)}")
        summary["Extraction"] = "OK"
    except Exception as e:
        print(f"  [!] Extraction Failed: {e}")
        summary["Extraction"] = "FAILED"

    # --- STEP 8: Chunking ---
    print("\nSTEP 8 — Chunking")
    try:
        sections = structure_analyzer.analyze_structure(text)
        chunks = chunker.chunk_text(sections, settings.CHUNK_SIZE, settings.CHUNK_OVERLAP)
        print(f"  Sections detected: {len(sections)}")
        print(f"  Chunks generated: {len(chunks)}")
        summary["Chunking"] = "OK"
    except Exception as e:
        print(f"  [!] Chunking Failed: {e}")
        summary["Chunking"] = "FAILED"

    # --- STEP 9: Embedding Generation ---
    print("\nSTEP 9 — Embedding Generation")
    try:
        model = embedder.get_model()
        texts = [c["chunk_text"] for c in chunks]
        embeddings = model.encode(texts).tolist()
        print(f"  Embedding dimension: {len(embeddings[0]) if embeddings else 0}")
        print(f"  Vectors generated: {len(embeddings)}")
        summary["Embedding"] = "OK"
    except Exception as e:
        print(f"  [!] Embedding Failed: {e}")
        summary["Embedding"] = "FAILED"

    # --- STEP 10: Vector Database Insert ---
    print("\nSTEP 10 — Vector Database Insert")
    try:
        # We need a section to hold chunks
        s_id = insert_section(supabase, doc_id, "Diagnostic Section", "Summary", [0.0]*384)
        inserted_count = 0
        for i, emb in enumerate(embeddings):
            if insert_document_chunk(supabase, s_id, texts[i], emb, i+1):
                inserted_count += 1
        print(f"  Rows inserted into document_chunks: {inserted_count}")
        summary["Vector Storage"] = "OK" if inserted_count == len(embeddings) else "PARTIAL"
    except Exception as e:
        print(f"  [!] Vector Insert Failed: {e}")
        summary["Vector Storage"] = "FAILED"

    # --- STEP 11: Final Status Update ---
    print("\nSTEP 11 — Final Status Update")
    try:
        # Simulate the transitions
        for state in ["chunking", "embedding", "ready"]:
            update_document_status(doc_id, state)
            print(f"  Transitioned to: {state}")
        
        # Verify final state
        res = supabase.table("documents").select("status").eq("doc_id", doc_id).execute()
        final_state = res.data[0]["status"] if res.data else "UNKNOWN"
        print(f"\nFinal Document State: {final_state}")
        print("Document ingestion completed successfully.")
        summary["Final Status"] = "OK" if final_state == "ready" else "FAILED"
    except Exception as e:
        print(f"  [!] Final Update Failed: {e}")
        summary["Final Status"] = "FAILED"

    # Clean up
    if os.path.exists(temp_local):
        os.remove(temp_local)

    print_final_summary(summary)

def print_final_summary(summary):
    print("\n" + "="*30)
    print("      FINAL DIAGNOSTIC SUMMARY")
    print("="*30)
    for key, val in summary.items():
        print(f"{key:<20}: {val}")
    print("="*30 + "\n")

if __name__ == "__main__":
    run_diagnostic()
