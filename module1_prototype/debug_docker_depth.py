import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from processing import storage

def check_docker_content():
    # 1. Get the document ID for Docker.pdf
    doc_res = storage.supabase.table("documents").select("id, filename").eq("filename", "Docker.pdf").execute()
    if not doc_res.data:
        print("Docker.pdf not found in database.")
        return
    
    doc_id = doc_res.data[0]['id']
    print(f"Document: Docker.pdf (ID: {doc_id})")
    
    # 2. Get all sections
    sec_res = storage.supabase.table("sections").select("id, section_title, section_summary").eq("document_id", doc_id).order("id").execute()
    print(f"\nSections Found: {len(sec_res.data)}")
    for s in sec_res.data:
        print(f" - [{s['id']}] {s['section_title']}")
        # print(f"   Summary: {s['section_summary'][:100]}...")

    # 3. Sample chunks for SSL configuration
    chunk_res = storage.supabase.table("document_chunks").select("content").ilike("content", "%ssl%").execute()
    print(f"\nChunks mentioning 'SSL': {len(chunk_res.data)}")
    for i, c in enumerate(chunk_res.data[:5]):
        print(f"  [{i}] {c['content'][:200]}...")

if __name__ == "__main__":
    check_docker_content()
