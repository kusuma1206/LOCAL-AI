from processing.storage import supabase
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

def check_data():
    try:
        # Check sections
        res = supabase.table("sections").select("*").limit(5).execute()
        print("--- SECTIONS ---")
        if res.data:
            for row in res.data:
                print(f"ID: {row['id']} | Title: {row['section_title']} | Summary Preview: {row['section_summary'][:50]}...")
        else:
            print("No sections found.")
            
        # Check chunks
        res = supabase.table("document_chunks").select("content").limit(5).execute()
        print("\n--- CHUNKS ---")
        if res.data:
            for row in res.data:
                print(f"Content Preview: {row['content'][:100]}...")
        else:
            print("No chunks found.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_data()
