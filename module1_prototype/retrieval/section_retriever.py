def retrieve_top_sections(supabase, query_embedding: list, top_n: int = 3, doc_ids: list[int] = None) -> list:
    """
    Retrieves the most similar sections using Supabase RPC 'match_sections'.
    """
    if not query_embedding:
        return []

    try:
        response = supabase.rpc("match_sections", {
            "query_embedding": query_embedding,
            "match_count": top_n,
            "document_ids": doc_ids  # Now accepts integer list
        }).execute()

        if not response.data:
            print("  [Section Retriever Warning] No similar sections found via RPC.")
            return []

        top_sections = []
        for row in response.data:
            top_sections.append({
                "section_id": row.get("id"),
                "document_id": row.get("doc_id"),  # Fixed: Integer doc_id from RPC
                "section_title": row.get("section_title"),
                "similarity_score": row.get("similarity")
            })

        print(f"  [Section Retriever] Sections retrieved via RPC (Found {len(top_sections)})")
        return top_sections

    except Exception as e:
        print(f"  [Section Retriever Failure] Error during RPC vector search: {e}")
        return []
