from processing import storage

def total_database_reset():
    supabase = storage.supabase
    
    print("WARNING: Starting TOTAL database reset...")
    
    # Tables to clear in order of dependency
    tables = ["query_logs", "document_chunks", "sections", "documents"]
    
    for table in tables:
        try:
            print(f"  Clearing table: {table}...")
            # Supabase Python SDK doesn't have a direct 'TRUNCATE' equivalent for all users,
            # so we use a filter that matches everything.
            # For most tables, we can delete based on existence.
            if table == "documents":
                # Need an ID filter for delete often, or use is_not NULL
                res = supabase.table(table).delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
            elif table == "query_logs":
                res = supabase.table(table).delete().neq("id", -1).execute()
            else:
                res = supabase.table(table).delete().neq("id", -1).execute()
            
            print(f"  [v] Table {table} cleared.")
        except Exception as e:
            print(f"  [!] Failed to clear table {table}: {e}")

    print("\nDatabase reset completed successfully.")

if __name__ == "__main__":
    total_database_reset()
