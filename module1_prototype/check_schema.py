from supabase import create_client, Client
import os

SUPABASE_URL = "https://vcaxpwrkhfbymgcyhvmk.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZjYXhwd3JraGZieW1nY3lodm1rIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzIwNzc1NTgsImV4cCI6MjA4NzY1MzU1OH0.f4LQHfzIoyNOoBTkLDuEljeLNcTY56XTX_6PE4Svygg"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    res = supabase.table("document_chunks").select("*").limit(1).execute()
    if res.data:
        print("Columns in document_chunks:", list(res.data[0].keys()))
    else:
        print("document_chunks is empty.")
except Exception as e:
    print("Error checking document_chunks:", e)

try:
    res = supabase.table("sections").select("*").limit(1).execute()
    if res.data:
        print("Columns in sections:", list(res.data[0].keys()))
    else:
        print("sections is empty.")
except Exception as e:
    print("Error checking sections:", e)
