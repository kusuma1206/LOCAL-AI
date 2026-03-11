import os
from dotenv import load_dotenv

# Ensure .env is loaded
load_dotenv()

"""
Configuration settings for the prototype.
"""

# Path configurations
INPUT_DOCS_DIR = "input_docs/"
VECTOR_STORE_PATH = "vector_store/"
ONEDRIVE_MOCK_DIR = "onedrive_mock/"

# Processing parameters
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# API Keys / Mock settings
EMBEDDING_MODEL = "text-embedding-ada-002"

# Validation thresholds
MIN_FILE_SIZE = 100  # bytes
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB
DUPLICATE_REGISTRY_PATH = "config/hash_registry.json"
SCANNED_PDF_THRESHOLD = 200  # min characters for real PDF

# SharePoint / Microsoft Graph Configuration
SHAREPOINT_TENANT_ID = os.getenv("SHAREPOINT_TENANT_ID", "your-tenant-id")
SHAREPOINT_CLIENT_ID = os.getenv("SHAREPOINT_CLIENT_ID", "your-client-id")
SHAREPOINT_CLIENT_SECRET = os.getenv("SHAREPOINT_CLIENT_SECRET", "your-client-secret")
SHAREPOINT_SITE_ID = os.getenv("SHAREPOINT_SITE_ID", "your-site-id")
SHAREPOINT_DRIVE_ID = os.getenv("SHAREPOINT_DRIVE_ID", "your-drive-id")
SHAREPOINT_BASE_FOLDER = "UploadedDocuments"
