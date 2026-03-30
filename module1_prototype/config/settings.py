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

# API Configuration
API_PORT = int(os.getenv("API_PORT", "8000"))
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# SharePoint / Microsoft Graph Configuration
SHAREPOINT_TENANT_ID = os.getenv("ONEDRIVE_TENANT_ID", "your-tenant-id")
SHAREPOINT_CLIENT_ID = os.getenv("ONEDRIVE_CLIENT_ID", "your-client-id")
SHAREPOINT_CLIENT_SECRET = os.getenv("ONEDRIVE_CLIENT_SECRET", "your-client-secret")
SHAREPOINT_SITE_ID = os.getenv("SHAREPOINT_SITE_ID", "your-site-id")
SHAREPOINT_DRIVE_ID = os.getenv("SHAREPOINT_DRIVE_ID", "your-drive-id")
SHAREPOINT_BASE_FOLDER = os.getenv("ONEDRIVE_FOLDER_NAME", "rag_documents")
ONEDRIVE_USER_ID = os.getenv("ONEDRIVE_USER_ID")

# Ingestion & Model Settings
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "384"))
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
