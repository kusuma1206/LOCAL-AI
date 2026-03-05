from processing.storage import supabase

try:
    print("Checking 'sections' table...")
    res = supabase.table("sections").select("id", "document_id", "section_title").limit(5).execute()
    print("Sections found:", res.data)
except Exception as e:
    print("Error querying sections:", e)

try:
    print("\nChecking 'document_chunks' table...")
    res = supabase.table("document_chunks").select("id", "section_id").limit(5).execute()
    print("Chunks found:", res.data)
except Exception as e:
    print("Error querying document_chunks:", e)

try:
    print("\nChecking 'query_logs' table...")
    res = supabase.table("query_logs").select("*").limit(5).execute()
    print("Query logs found:", res.data)
except Exception as e:
    print("Error querying query_logs:", e)
