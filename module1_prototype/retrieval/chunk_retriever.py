def retrieve_top_chunks(supabase, query_embedding: list, section_ids: list, top_k: int = 5) -> list:
    """
    Retrieves the most similar chunks from document_chunks, filtered by a list of section_ids.
    This function expects an 'match_chunks' RPC defined in the Supabase instance.
    """
    if not query_embedding or not section_ids:
        return []

    try:
        # Performing semantic search via Supabase RPC (Stored Procedure)
        # The 'match_chunks' RPC handles filtering by section_ids and vector similarity.
        response = supabase.rpc("match_chunks", {
            "query_embedding": query_embedding,
            "match_count": top_k,
            "section_ids": section_ids
        }).execute()

        if not response.data:
            print("  [Chunk Retriever Warning] No similar chunks found within selected sections.")
            return []

        # Map results to expected keys
        top_chunks = []
        for row in response.data:
            top_chunks.append({
                "chunk_text": row.get("content"),
                "section_id": row.get("section_id"),
                "similarity_score": row.get("similarity")
            })

        print(f"  [Chunk Retriever] Chunks retrieved via RPC (Found {len(top_chunks)})")
        return top_chunks

    except Exception as e:
        print(f"  [Chunk Retriever Failure] Error during chunk retrieval: {e}")
        return []
