def retrieve_top_sections(supabase, query_embedding: list, top_n: int = 3) -> list:
    """
    Retrieves the most similar sections using Supabase RPC 'match_sections'.
    This is the safest way to perform vector similarity search with pgvector in Supabase.
    """
    if not query_embedding:
        return []

    try:
        # Reverting to RPC 'match_sections' as direct .order() with pgvector operator is not supported via PostgREST
        response = supabase.rpc("match_sections", {
            "query_embedding": query_embedding,
            "match_count": top_n
        }).execute()

        if not response.data:
            print("  [Section Retriever Warning] No similar sections found via RPC.")
            return []

        top_sections = []
        for row in response.data:
            top_sections.append({
                "section_id": row.get("id"),
                "document_id": row.get("document_id"),
                "section_title": row.get("section_title"),
                "similarity_score": row.get("similarity")
            })

        print(f"  [Section Retriever] Sections retrieved via RPC (Found {len(top_sections)})")
        return top_sections

    except Exception as e:
        print(f"  [Section Retriever Failure] Error during RPC vector search: {e}")
        return []
