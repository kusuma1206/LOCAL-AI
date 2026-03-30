from supabase import create_client, Client
import sys
import os
from config import settings

# Supabase Config from settings (loaded from .env)
SUPABASE_URL = settings.SUPABASE_URL
SUPABASE_KEY = settings.SUPABASE_KEY

if not SUPABASE_URL or not SUPABASE_KEY:
    print("  [Critical Error] SUPABASE_URL or SUPABASE_KEY not found in environment!")
    sys.exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    res = supabase.table("document_chunks").select("*").limit(1).execute()
    if res.data:
        print("\n--- document_chunks (Row 1) ---")
        print(res.data[0])
    else:
        print("document_chunks is empty.")
except Exception as e:
    print("Error checking document_chunks:", e)

try:
    res = supabase.table("sections").select("*").limit(1).execute()
    if res.data:
        print("\n--- sections (Row 1) ---")
        print(res.data[0])
    else:
        print("sections is empty.")
except Exception as e:
    print("Error checking sections:", e)

try:
    res = supabase.table("documents").select("*").limit(1).execute()
    if res.data:
        print("\n--- documents (Row 1) ---")
        # Embedding might be long, slice it
        row = res.data[0].copy()
        if 'document_embedding' in row and row['document_embedding']:
            row['document_embedding'] = str(row['document_embedding'])[:50] + "..."
        print(row)
    else:
        print("documents is empty.")
except Exception as e:
    print("Error checking documents:", e)
