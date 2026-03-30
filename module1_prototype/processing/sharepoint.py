import os
import requests
from config import settings

def get_onedrive_access_token(tenant_id, client_id, client_secret):
    """
    Acquires an access token using direct Microsoft OAuth2 client credentials flow.
    """
    url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "https://graph.microsoft.com/.default",
        "grant_type": "client_credentials"
    }
    
    response = requests.post(url, headers=headers, data=data)
    
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        error_info = response.json()
        error = error_info.get("error")
        error_desc = error_info.get("error_description")
        raise Exception(f"Failed to acquire token: {error} - {error_desc}")

def upload_to_onedrive(file_bytes, filename, doc_id):
    """
    Uploads file bytes to OneDrive under the user-specific 'rag_documents' folder.
    Steps:
    1. Get token.
    2. Format filename: doc_{doc_id}_{filename}
    3. PUT to Graph API using user-specific endpoint.
    """
    tenant_id = settings.SHAREPOINT_TENANT_ID
    client_id = settings.SHAREPOINT_CLIENT_ID
    client_secret = settings.SHAREPOINT_CLIENT_SECRET
    user_id = settings.ONEDRIVE_USER_ID
    folder = settings.SHAREPOINT_BASE_FOLDER
    
    if not user_id:
        raise Exception("ONEDRIVE_USER_ID not configured in environment.")

    token = get_onedrive_access_token(tenant_id, client_id, client_secret)
    
    # Construct filename
    clean_filename = f"doc_{doc_id}_{filename}"
    
    # User-specific endpoint: /users/{user_id}/drive/root:/{folder}/{filename}:/content
    url = f"https://graph.microsoft.com/v1.0/users/{user_id}/drive/root:/{folder}/{clean_filename}:/content"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/octet-stream"
    }
    
    response = requests.put(url, headers=headers, data=file_bytes)
    
    if response.status_code in [200, 201]:
        upload_data = response.json()
        item_id = upload_data.get("id")
        
        # Step 4: Create a shareable link (Anonymous View)
        # POST /users/{user_id}/drive/items/{item_id}/createLink
        share_url = f"https://graph.microsoft.com/v1.0/users/{user_id}/drive/items/{item_id}/createLink"
        share_headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        share_data = {
            "type": "view",
            "scope": "anonymous"
        }
        
        share_response = requests.post(share_url, headers=share_headers, json=share_data)
        
        if share_response.status_code in [200, 201]:
            share_info = share_response.json()
            # The shareable link is in the 'link' object
            guest_url = share_info.get("link", {}).get("webUrl")
            return {
                "webUrl": guest_url,
                "id": item_id
            }
        else:
            print(f"  [Warning] Link creation failed: {share_response.text}")
            # Fallback to the default non-shareable webUrl if link creation fails
            return {
                "webUrl": upload_data.get("webUrl"),
                "id": item_id
            }
    else:
        raise Exception(f"OneDrive upload failed: {response.status_code} - {response.text}")

def download_from_onedrive(onedrive_item_id_or_url):
    """
    Downloads file content from OneDrive using Microsoft Graph.
    Can accept a webUrl (personal link) or a Drive Item ID.
    For this implementation, we'll assume we need to resolve the item first if given a URL,
    but since we have the ID from the upload response, we'll favor that.
    """
    tenant_id = settings.SHAREPOINT_TENANT_ID
    client_id = settings.SHAREPOINT_CLIENT_ID
    client_secret = settings.SHAREPOINT_CLIENT_SECRET
    user_id = settings.ONEDRIVE_USER_ID
    
    token = get_onedrive_access_token(tenant_id, client_id, client_secret)
    headers = {"Authorization": f"Bearer {token}"}

    # If it's a full URL, we try to extract the ID or use the share link API
    # But often it's easier to just use the Item ID if provided.
    # For now, we'll implement the logic to download via item ID or the specific path.
    # Given the user flow, we might just have the webUrl.
    
    # Simple path-based download if we can't resolve ID easily:
    # GET /users/{id}/drive/items/{item-id}/content
    
    # If it looks like an ID (no slashes/dots), use item-id endpoint
    if "/" not in onedrive_item_id_or_url and "." not in onedrive_item_id_or_url:
        url = f"https://graph.microsoft.com/v1.0/users/{user_id}/drive/items/{onedrive_item_id_or_url}/content"
    else:
        # Fallback: Parse item ID from the URL or use a different Graph API
        # For this prototype, we'll try to find the item by name in the known folder if it's a name
        # However, the most robust way in a Service Principal context is using the Item ID.
        # Let's assume the input is the Item ID for now as per the upload return.
        url = f"https://graph.microsoft.com/v1.0/users/{user_id}/drive/items/{onedrive_item_id_or_url}/content"

    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.content
    else:
        raise Exception(f"OneDrive download failed: {response.status_code} - {response.text}")

class SharePointService:
    """
    Handles file uploads to SharePoint via Microsoft Graph API.
    """
    def __init__(self):
        self.client_id = settings.SHAREPOINT_CLIENT_ID
        self.client_secret = settings.SHAREPOINT_CLIENT_SECRET
        self.tenant_id = settings.SHAREPOINT_TENANT_ID
        self.site_id = settings.SHAREPOINT_SITE_ID
        self.drive_id = settings.SHAREPOINT_DRIVE_ID
        self.base_folder = settings.SHAREPOINT_BASE_FOLDER
        
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.scopes = ["https://graph.microsoft.com/.default"]
        
    def get_access_token(self):
        """
        Acquires an access token using the new shared function.
        """
        return get_onedrive_access_token(
            self.tenant_id,
            self.client_id,
            self.client_secret
        )

    def upload_file(self, file_path, remote_filename=None):
        """
        Uploads a local file to the configured SharePoint drive.
        """
        if not remote_filename:
            remote_filename = os.path.basename(file_path)
            
        token = self.get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/octet-stream"
        }
        
        # URL format for drive item upload
        # https://graph.microsoft.com/v1.0/sites/{site-id}/drives/{drive-id}/root:/{folder}/{filename}:/content
        upload_url = f"https://graph.microsoft.com/v1.0/sites/{self.site_id}/drives/{self.drive_id}/root:/{self.base_folder}/{remote_filename}:/content"
        
        with open(file_path, "rb") as f:
            file_content = f.read()
            
        response = requests.put(upload_url, headers=headers, data=file_content)
        
        if response.status_code in [200, 201]:
            data = response.json()
            return {
                "sharepoint_url": data.get("webUrl"),
                "sharepoint_file_id": data.get("id")
            }
        else:
            raise Exception(f"SharePoint upload failed: {response.status_code} - {response.text}")
