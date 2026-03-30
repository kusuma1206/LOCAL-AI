def retrieve_top_documents(supabase, query_embedding: list, top_k: int = 3) -> list:
    """
    Retrieves the most similar documents using the 'match_documents' RPC.
    """
    if not query_embedding:
        return []

    try:
        # Note: RPC should return 'doc_id', 'title', 'filename', and 'similarity'
        response = supabase.rpc("match_documents", {
            "query_embedding": query_embedding,
            "match_count": top_k
        }).execute()

        if response.data:
            top_docs = []
            for row in response.data:
                top_docs.append({
                    "doc_id": row.get("doc_id"),
                    "filename": row.get("filename"),
                    "title": row.get("title"),
                    "similarity_score": row.get("similarity")
                })

            print(f"  [Document Retriever] Found {len(top_docs)} relevant documents via RPC.")
            return top_docs

    except Exception as e:
        print(f"  [Document Retriever Warning] RPC matching failed, using Python fallback: {e}")

    # --- Python Fallback Logic ---
    try:
        import numpy as np
        import ast

        # 1. Fetch all documents using new schema
        res = supabase.table("documents").select("doc_id, filename, title, document_summary, document_embedding").execute()
        
        if not res.data:
            print("  [Document Retriever Failure] No documents found in database.")
            return []

        q_vec = np.array(query_embedding).astype('float32')
        q_norm = np.linalg.norm(q_vec)
        
        if q_norm == 0:
            return []

        results = []
        for doc in res.data:
            raw_emb = doc.get("document_embedding")
            if not raw_emb:
                continue
                
            if isinstance(raw_emb, str):
                try:
                    raw_emb = ast.literal_eval(raw_emb)
                except:
                    continue
            
            d_vec = np.array(raw_emb).astype('float32')
            if len(d_vec) == 0:
                continue
                
            d_norm = np.linalg.norm(d_vec)
            if d_norm == 0:
                continue
                
            # Compute Cosine Similarity
            sim = np.dot(q_vec, d_vec) / (q_norm * d_norm)
            
            results.append({
                "doc_id": doc.get("doc_id"),
                "filename": doc.get("filename"),
                "title": doc.get("title"),
                "similarity_score": float(sim)
            })

        # Sort by highest similarity
        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        top_docs = results[:top_k]
        
        print(f"  [Document Retriever Debug] Fallback results: {[ (d['filename'], d['similarity_score']) for d in top_docs]}")
        print(f"  [Document Retriever] Found {len(top_docs)} documents via Python fallback.")
        return top_docs

    except Exception as e:
        import traceback
        print(f"  [Document Retriever Failure] Python fallback failed: {e}\n{traceback.format_exc()}")
        return []

def get_top_document(supabase, query_embedding: list, top_k_chunks: int = 15) -> int:
    """
    Retrieves the most relevant document ID based on weighted voting across:
    1. Direct document matches (Weight: 3.0)
    2. Section matches (Weight: 2.0)
    3. Chunk hits (Weight: 1.0)
    """
    if not query_embedding:
        return None
        
    try:
        results = {}

        # 1. Level 1: Document Match
        try:
            doc_res = supabase.rpc("match_documents", {
                "query_embedding": query_embedding,
                "match_count": 3
            }).execute()
            if doc_res.data:
                for d in doc_res.data:
                    doc_id = d.get("doc_id")
                    score = d.get("similarity", 0) * 3.0
                    results[doc_id] = results.get(doc_id, 0) + score
        except: pass

        # 2. Level 2: Section Match
        try:
            sec_res = supabase.rpc("match_sections", {
                "query_embedding": query_embedding,
                "match_count": 5
            }).execute()
            if sec_res.data:
                for s in sec_res.data:
                    doc_id = s.get("document_id")
                    score = s.get("similarity", 0) * 2.0
                    results[doc_id] = results.get(doc_id, 0) + score
        except: pass

        # 3. Level 3: Chunk Match
        try:
            from processing.storage import search_chunks
            chunks = search_chunks(supabase, query_embedding, top_k=top_k_chunks)
            if chunks:
                # Map chunks to docs via sections
                sec_ids = list(set([c["section_id"] for c in chunks if c.get("section_id")]))
                sec_map = supabase.table("sections").select("section_id, document_id").in_("section_id", sec_ids).execute()
                sec_to_doc = {r["section_id"]: r["document_id"] for r in sec_map.data} if sec_map.data else {}
                
                for c in chunks:
                    doc_id = sec_to_doc.get(c.get("section_id"))
                    if doc_id:
                        score = c.get("similarity_score", 0) * 1.0
                        results[doc_id] = results.get(doc_id, 0) + score
        except: pass

        if results:
            top_doc = max(results.items(), key=lambda x: x[1])
            print(f"  [Multi-Level Scorer] Weighted Voting Results: {results}")
            print(f"  [Multi-Level Scorer] Decided top document {top_doc[0]} (Score: {top_doc[1]:.4f})")
            return top_doc[0]
            
        return None
        
    except Exception as e:
        import traceback
        print(f"  [Multi-Level Scorer Failure] Error scoring top document: {e}\n{traceback.format_exc()}")
        return None

def retrieve_document_sections(supabase, doc_id: int) -> str:
    """
    Retrieves all sections belonging to a specific document, ordered by section_order,
    then expands each section into a full cohesive document explanation.
    """
    from processing.storage import expand_section
    
    try:
        # Retrieve sections linked to doc_id using NEW schema
        res = supabase.table("sections") \
            .select("section_id, title, section_order") \
            .eq("document_id", doc_id) \
            .order("section_order") \
            .execute()
            
        if not res.data:
            print(f"  [Document Retriever] No sections found for doc_id {doc_id}")
            return ""
            
        sections = res.data
        
        full_document_text = []
        
        for sec in sections:
            sec_id = sec.get("section_id")
            title = sec.get("title", "Unknown Section")
            
            # Fetch all matching chunks and merge them via our expand_section helper
            section_content = expand_section(sec_id)
            
            if section_content:
                # Format into structured block
                full_document_text.append(f"## {title}\n\n{section_content}\n")
                
        # Combine all sections
        return "\n".join(full_document_text)

    except Exception as e:
        print(f"  [Document Retriever Failure] Error retrieving overview sections: {e}")
        return ""

    except Exception as e:
        print(f"  [Document Retriever Failure] Error retrieving overview sections: {e}")
        return ""
