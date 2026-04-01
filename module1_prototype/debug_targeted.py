import os
import sys
import codecs
from dotenv import load_dotenv
sys.path.append(os.getcwd())

from processing.storage import supabase

def debug_retrieval():
    output_lines = []
    output_lines.append("--- Targeted Debugging Retrieval Issue ---\n")
    
    # 1. Check for Doc ID 81 specifically
    doc_81_id = "81"
    output_lines.append(f"\n1. Checking for Doc ID {doc_81_id}:\n")
    res_81 = supabase.table("documents").select("*").eq("doc_id", doc_81_id).execute()
    if res_81.data:
        doc = res_81.data[0]
        output_lines.append(f"   Found Doc 81: {doc['title']} ({doc['filename']})\n")
        
        # Check sections for Doc 81
        res_sec_81 = supabase.table("sections").select("section_id, title").eq("document_id", doc_81_id).execute()
        output_lines.append(f"   Sections in Doc 81 ({len(res_sec_81.data)}):\n")
        for s in res_sec_81.data:
            output_lines.append(f"      - {s['title']} ({s['section_id']})\n")
    else:
        output_lines.append(f"   Doc ID {doc_81_id} NOT found in documents table.\n")

    # 2. Search for "phanendra" in all document titles/filenames
    output_lines.append("\n2. Searching for 'phanendra' in document metadata:\n")
    res_phan_docs = supabase.table("documents").select("doc_id, title, filename").ilike("filename", "%phanendra%").execute()
    for d in res_phan_docs.data:
        output_lines.append(f"   - {d['doc_id']}: {d['title']} ({d['filename']})\n")
    
    # 3. Vector search for the query
    output_lines.append("\n3. Vector Search for 'performance evaluation profile of phanendra':\n")
    from retrieval.query_embedder import generate_query_embedding
    from processing.storage import search_chunks
    
    query = "performance evaluation profile of phanendra"
    embedding = generate_query_embedding(query)
    if embedding:
        chunks = search_chunks(supabase, embedding, top_k=5)
        for i, chunk in enumerate(chunks):
            sec_id = chunk.get('section_id')
            score = chunk.get('similarity_score', 0)
            
            s_res = supabase.table("sections").select("document_id, title").eq("section_id", sec_id).execute()
            if s_res.data:
                d_id = s_res.data[0]['document_id']
                sec_title = s_res.data[0]['title']
                d_res = supabase.table("documents").select("filename").eq("doc_id", d_id).execute()
                fname = d_res.data[0]['filename'] if d_res.data else "Unknown"
                output_lines.append(f"   Match {i+1}: {score:.4f} -> Doc: {fname} (ID: {d_id}), Section: {sec_title}\n")
            else:
                output_lines.append(f"   Match {i+1}: {score:.4f} -> Unknown Section {sec_id}\n")

    with codecs.open("c:\\Users\\Kusuma\\OneDrive\\Desktop\\NO\\LOCAL-AI\\module1_prototype\\debug_targeted.txt", "w", "utf-8") as f:
        f.writelines(output_lines)

if __name__ == "__main__":
    debug_retrieval()
