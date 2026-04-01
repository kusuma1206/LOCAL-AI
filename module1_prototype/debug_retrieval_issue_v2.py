import os
import sys
import codecs
from dotenv import load_dotenv
sys.path.append(os.getcwd())

from processing.storage import supabase

def debug_retrieval():
    output_lines = []
    output_lines.append("--- Debugging Retrieval Issue (UTF-8 File) ---\n")
    
    # 1. Search for "phanendra" in documents table
    output_lines.append("\n1. Searching for 'phanendra' or 'ID 81' in 'documents' table:\n")
    res_docs = supabase.table("documents").select("*").execute()
    for doc in res_docs.data:
        if "phanendra" in str(doc.get('filename', '')).lower() or "phanendra" in str(doc.get('title', '')).lower() or str(doc.get('doc_id')) == '81':
            output_lines.append(f"   ID: {doc['doc_id']}, Title: {doc['title']}, Filename: {doc['filename']}\n")

    # 2. Search for "phanendra" in sections table
    output_lines.append("\n2. Searching for 'phanendra' in 'sections' table:\n")
    res_sec = supabase.table("sections").select("*").execute()
    for sec in res_sec.data:
        if "phanendra" in str(sec.get('title', '')).lower() or "phanendra" in str(sec.get('section_summary', '')).lower():
            output_lines.append(f"   Section ID: {sec['section_id']}, Doc ID: {sec['document_id']}, Title: {sec['title']}\n")

    # 3. Check Doc ID 34
    output_lines.append("\n3. Checking Doc ID 34:\n")
    for doc in res_docs.data:
        if str(doc.get('doc_id')) == '34':
            output_lines.append(f"   ID 34: {doc['title']} ({doc['filename']})\n")
    
    # 5. Check vector search for "performance evaluation profile of phanendra"
    output_lines.append("\n5. Simulating Vector Search for 'performance evaluation profile of phanendra':\n")
    from retrieval.query_embedder import generate_query_embedding
    from processing.storage import search_chunks
    
    query = "performance evaluation profile of phanendra"
    embedding = generate_query_embedding(query)
    if embedding:
        chunks = search_chunks(supabase, embedding, top_k=10)
        for i, chunk in enumerate(chunks):
            sec_id = chunk.get('section_id')
            score = chunk.get('similarity_score', 0)
            
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
            
            output_lines.append(f"   Match {i+1}: Score: {score:.4f}, Doc: {doc_info} ({d_id}), Section: {section_info}\n")

    with codecs.open("c:\\Users\\Kusuma\\OneDrive\\Desktop\\NO\\LOCAL-AI\\module1_prototype\\debug_utf8.txt", "w", "utf-8") as f:
        f.writelines(output_lines)

if __name__ == "__main__":
    debug_retrieval()
