import os
from dotenv import load_dotenv
from config import settings

def test_loading():
    print("--- Testing Environment Variable Loading ---")
    
    # 1. Test direct loading
    load_dotenv()
    client_id_env = os.getenv("ONEDRIVE_CLIENT_ID")
    print(f"Direct os.getenv('ONEDRIVE_CLIENT_ID'): {'FOUND' if client_id_env else 'NOT FOUND'}")
    
    # 2. Test settings mapping
    print(f"settings.SHAREPOINT_CLIENT_ID: {'MATCH' if settings.SHAREPOINT_CLIENT_ID == client_id_env else 'MISMATCH'}")
    print(f"settings.SHAREPOINT_BASE_FOLDER: {settings.SHAREPOINT_BASE_FOLDER}")
    
    if client_id_env and settings.SHAREPOINT_CLIENT_ID == client_id_env:
        print("\nSUCCESS: Environment variables are correctly loaded and mapped.")
    else:
        print("\nFAILURE: Environment variables were not loaded correctly.")

if __name__ == "__main__":
    test_loading()
