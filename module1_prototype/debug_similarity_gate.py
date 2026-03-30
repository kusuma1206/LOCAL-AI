from processing.storage import supabase

# Search for "Similarity Gate" in chunks
res = supabase.table("document_chunks").select("content, section_id").ilike("content", "%Similarity Gate%").execute()
print(f"Found {len(res.data)} chunks containing 'Similarity Gate':")
for r in res.data:
    # Get document id from section
    sec_res = supabase.table("sections").select("document_id").eq("section_id", r["section_id"]).execute()
    if not sec_res.data:
        continue
    doc_id = sec_res.data[0]["document_id"]
    # Get document name
    doc_res = supabase.table("documents").select("filename").eq("doc_id", doc_id).execute()
    doc_name = doc_res.data[0]["filename"] if doc_res.data else "Unknown"
    print(f"- Doc: {doc_name} (ID: {doc_id}), Section: {r['section_id']}")
    print(f"  Content: {r['content'][:100]}...")
    print("-" * 20)
