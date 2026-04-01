import os
import sys
import codecs
from dotenv import load_dotenv
sys.path.append(os.getcwd())

# Ensure stdout uses UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

from processing.storage import supabase

def debug_retrieval():
    print("--- Debugging Retrieval Issue (UTF-8) ---")
    
    # 1. Search for "phanendra" in documents table
    print("\n1. Searching for 'phanendra' or 'ID 81' in 'documents' table:")
    res_docs = supabase.table("documents").select("*").execute()
    found_docs = []
    for doc in res_docs.data:
        # doc_id is typically UUID but user says 81. Let's check both
        if "phanendra" in str(doc.get('filename', '')).lower() or "phanendra" in str(doc.get('title', '')).lower() or str(doc.get('doc_id')) == '81':
            print(f"   ID: {doc['doc_id']}, Title: {doc['title']}, Filename: {doc['filename']}")
            found_docs.append(doc)

    # 2. Search for "phanendra" in sections table
    print("\n2. Searching for 'phanendra' in 'sections' table:")
    res_sec = supabase.table("sections").select("*").execute()
    for sec in res_sec.data:
        if "phanendra" in str(sec.get('title', '')).lower() or "phanendra" in str(sec.get('section_summary', '')).lower():
            print(f"   Section ID: {sec['section_id']}, Doc ID: {sec['document_id']}, Title: {sec['title']}")

    # 3. Check Doc ID 34
    print("\n3. Checking Doc ID 34:")
    for doc in res_docs.data:
        if str(doc.get('doc_id')) == '34':
            print(f"   ID 34: {doc['title']} ({doc['filename']})")
    
    # 5. Check vector search for "performance evaluation profile of phanendra"
    print("\n5. Simulating Vector Search for 'performance evaluation profile of phanendra':")
    from retrieval.query_embedder import generate_query_embedding
    from processing.storage import search_chunks
    
    query = "performance evaluation profile of phanendra"
    embedding = generate_query_embedding(query)
    if embedding:
        chunks = search_chunks(supabase, embedding, top_k=10)
        for i, chunk in enumerate(chunks):
            sec_id = chunk.get('section_id')
            score = chunk.get('similarity_score', 0)
            
            # Get document and section info
            section_info = "Unknown Section"
            doc_info = "Unknown Doc"
            d_id = "Unknown ID"
            
            if sec_id:
                s_res = supabase.table("sections").select("document_id, title").eq("section_id", sec_id).execute()
                if s_res.data:
                    d_id = s_res.data[0]['document_id']
                    section_info = s_res.data[0]['title']
                    d_res = supabase.table("documents").select("filename").eq("doc_id", d_id).execute()
                    if d_res.data:
                        doc_info = d_res.data[0]['filename']
            
            print(f"   Match {i+1}: Score: {score:.4f}, Doc: {doc_info} ({d_id}), Section: {section_info}")

if __name__ == "__main__":
    debug_retrieval()
