from processing import storage

def cleanup_legacy_records():
    supabase = storage.supabase
    
    print("Fetching documents...")
    res = supabase.table("documents").select("id, filename").execute()
    
    legacy_ids = []
    for doc in res.data:
        doc_id = str(doc['id'])
        if len(doc_id) != 36: # Not a standard UUID
            print(f"Flagged legacy ID: {doc_id} ({doc['filename']})")
            legacy_ids.append(doc_id)
            
    if not legacy_ids:
        print("No legacy (non-UUID) records found in 'documents' table.")
    else:
        for lid in legacy_ids:
            print(f"Cleaning up records for legacy ID: {lid}")
            # storage.delete_document_records handles section/chunk deletion
            storage.delete_document_records(supabase, lid)
            # Delete the document entry itself
            supabase.table("documents").delete().eq("id", lid).execute()
            print(f"Successfully removed legacy ID: {lid}")

    # Also check sections for orphaned legacy IDs
    print("\nChecking for orphaned legacy sections...")
    sec_res = supabase.table("sections").select("id, document_id").execute()
    orphaned_sections = []
    for sec in sec_res.data:
        doc_id = str(sec['document_id'])
        if len(doc_id) != 36:
            orphaned_sections.append(sec['id'])
            
    if orphaned_sections:
        print(f"Found {len(orphaned_sections)} orphaned legacy sections. Cleaning up chunks...")
        supabase.table("document_chunks").delete().in_("section_id", orphaned_sections).execute()
        print("Cleaning up sections...")
        supabase.table("sections").delete().in_("id", orphaned_sections).execute()
        print("Done.")
    else:
        print("No orphaned legacy sections found.")

if __name__ == "__main__":
    cleanup_legacy_records()
