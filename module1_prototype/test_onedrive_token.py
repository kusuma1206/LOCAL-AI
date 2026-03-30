import os
from dotenv import load_dotenv
from processing.sharepoint import get_onedrive_access_token

def test_token_flow():
    load_dotenv()
    tenant_id = os.getenv("ONEDRIVE_TENANT_ID")
    client_id = os.getenv("ONEDRIVE_CLIENT_ID")
    client_secret = os.getenv("ONEDRIVE_CLIENT_SECRET")
    
    print("--- Testing OneDrive OAuth Token Flow ---")
    print(f"Tenant ID: {tenant_id}")
    print(f"Client ID: {client_id}")
    
    try:
        token = get_onedrive_access_token(tenant_id, client_id, client_secret)
        if token:
            print("\nSUCCESS: Token acquired successfully!")
            print(f"Token length: {len(token)}")
            # Optional: Show prefix for manual check
            print(f"Token prefix: {token[:10]}...")
        else:
            print("\nFAILURE: Function returned empty token.")
    except Exception as e:
        print(f"\nERROR: {e}")

if __name__ == "__main__":
    test_token_flow()
