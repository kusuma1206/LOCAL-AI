import os
from dotenv import load_dotenv
from processing.sharepoint import upload_to_onedrive

def test_upload_flow():
    load_dotenv()
    
    print("--- Testing OneDrive Upload Function ---")
    
    # Create a small dummy file in memory
    test_content = b"This is a test document for Sakhi RAG OneDrive Upload."
    test_filename = "test_upload_logic.txt"
    test_doc_id = 99
    
    print(f"Uploading file: {test_filename} (doc_id: {test_doc_id})")
    
    with open("upload_test_results.txt", "w", encoding="utf-8") as log:
        log.write("--- OneDrive Upload Test Log ---\n")
        try:
            result = upload_to_onedrive(test_content, test_filename, test_doc_id)
            if result:
                log.write("SUCCESS: File uploaded successfully!\n")
                log.write(f"Web URL: {result.get('webUrl')}\n")
                log.write(f"Graph ID: {result.get('id')}\n")
                print("\nSUCCESS: See upload_test_results.txt")
            else:
                log.write("FAILURE: Function returned empty result.\n")
        except Exception as e:
            log.write(f"ERROR: {e}\n")
            print(f"\nERROR: See upload_test_results.txt")

if __name__ == "__main__":
    test_upload_flow()
