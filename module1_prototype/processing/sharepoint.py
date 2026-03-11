import os
import requests
import msal
from config import settings

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
        Acquires an access token using Client Credentials Flow.
        """
        app = msal.ConfidentialClientApplication(
            self.client_id,
            authority=self.authority,
            client_credential=self.client_secret
        )
        
        result = app.acquire_token_silent(self.scopes, account=None)
        if not result:
            result = app.acquire_token_for_client(scopes=self.scopes)
            
        if "access_token" in result:
            return result["access_token"]
        else:
            error = result.get("error")
            error_desc = result.get("error_description")
            raise Exception(f"Failed to acquire token: {error} - {error_desc}")

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
