from supabase import create_client, Client
import os

SUPABASE_URL = "https://vcaxpwrkhfbymgcyhvmk.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZjYXhwd3JraGZieW1nY3lodm1rIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzIwNzc1NTgsImV4cCI6MjA4NzY1MzU1OH0.f4LQHfzIoyNOoBTkLDuEljeLNcTY56XTX_6PE4Svygg"

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
