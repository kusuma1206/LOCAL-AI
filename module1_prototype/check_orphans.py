from processing.storage import supabase

def check_orphans():
    try:
        # Get all section IDs that HAVE chunks in nollm table
        res = supabase.table("document_chunks").select("section_id").execute()
        linked_section_ids = list(set([row["section_id"] for row in res.data]))
        print(f"Section IDs with chunks in nollm: {linked_section_ids}")
        
        # Get the titles of these sections
        if linked_section_ids:
            secs_res = supabase.table("sections").select("id", "section_title").in_("id", linked_section_ids).execute()
            for row in secs_res.data:
                print(f" - [{row['id']}] {row['section_title']}")
        else:
            print("No linked sections found.")
            
    except Exception as e:
        print(f"Error checking orphans: {e}")

if __name__ == "__main__":
    check_orphans()
