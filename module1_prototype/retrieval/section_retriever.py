def retrieve_top_sections(supabase, query_embedding: list, top_n: int = 3, doc_ids: list[int] = None) -> list:
    """
    Retrieves the most similar sections using Supabase RPC 'match_sections'.
    """
    if not query_embedding:
        return []

    try:
        # Note: RPC should be updated in Supabase to return 'section_id', 'document_id', 'title'
        response = supabase.rpc("match_sections", {
            "query_embedding": query_embedding,
            "match_count": top_n,
            "document_ids": doc_ids
        }).execute()

        if response.data:
            top_sections = []
            print(f"  [Section Retriever] Retrieved {len(response.data)} sections via RPC")
            for row in response.data:
                score = row.get("similarity")
                title = row.get("title") or row.get("section_title")
                print(f"  [Section Retriever] Similarity {score:.4f} \u2192 {title}")
                
                top_sections.append({
                    "section_id": row.get("section_id") or row.get("id"),
                    "document_id": row.get("document_id") or row.get("doc_id"),
                    "section_title": title,
                    "similarity_score": score
                })
            return top_sections

    except Exception as e:
        print(f"  [Section Retriever Warning] RPC matching failed, using Python fallback: {e}")

    # --- Python Fallback Logic ---
    try:
        import numpy as np
        import ast

        # 1. Fetch sections filtered by doc_ids if provided
        # Use new schema column names: section_id, document_id, title, section_embedding
        query = supabase.table("sections").select("section_id, document_id, title, section_embedding")
        if doc_ids:
            query = query.in_("document_id", doc_ids)
            
        res = query.execute()
        
        if not res.data:
            print("  [Section Retriever Failure] No sections found in database.")
            return []

        print(f"  [Section Retriever] Fetched {len(res.data)} sections from DB for fallback search.")

        q_vec = np.array(query_embedding).astype('float32')
        q_norm = np.linalg.norm(q_vec)
        
        if q_norm == 0:
            return []

        results = []
        for sec in res.data:
            raw_emb = sec.get("section_embedding")
            if not raw_emb:
                continue
                
            # Handle possible string storage although we aim for proper Vector type
            if isinstance(raw_emb, str):
                try:
                    raw_emb = ast.literal_eval(raw_emb)
                except:
                    continue
            
            s_vec = np.array(raw_emb).astype('float32')
            if len(s_vec) == 0:
                continue
                
            s_norm = np.linalg.norm(s_vec)
            if s_norm == 0:
                continue
                
            # Compute Cosine Similarity
            sim = np.dot(q_vec, s_vec) / (q_norm * s_norm)
            
            results.append({
                "section_id": sec.get("section_id"),
                "document_id": sec.get("document_id"),
                "section_title": sec.get("title"),
                "similarity_score": float(sim)
            })

        # Sort by highest similarity
        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        top_sections = results[:top_n]
        
        print(f"  [Section Retriever] Retrieved {len(top_sections)} top sections via fallback")
        for s in top_sections:
            print(f"  [Section Retriever] Similarity {s['similarity_score']:.4f} \u2192 {s['section_title']}")
            
        return top_sections

    except Exception as e:
        import traceback
        print(f"  [Section Retriever Failure] Python fallback failed: {e}\n{traceback.format_exc()}")
        return []
