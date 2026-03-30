from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def check_columns(table_name):
    print(f"\n--- Columns in {table_name} ---")
    try:
        res = supabase.table(table_name).select("*").limit(1).execute()
        if res.data:
            print("Row found, columns are:")
            print(list(res.data[0].keys()))
        else:
            print(f"Table {table_name} is empty, but let's try to fetch an empty row to see columns...")
            # Sometimes select("*") works even if empty to see if it triggers an error or shows keys if data exists
            print("Table empty.")
    except Exception as e:
        print(f"Error checking {table_name}: {e}")

if __name__ == "__main__":
    check_columns("documents")
    check_columns("sections")
