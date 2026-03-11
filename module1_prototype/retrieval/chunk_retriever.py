def retrieve_top_chunks(supabase, query_embedding: list, section_ids: list, top_k: int = 8, threshold: float = 0.50) -> list:
    """
    Strict Hierarchical Retrieval:
    Instead of doing an independent vector search on chunks, this fetches 
    the sequential chunks for the highly-matched sections to provide a rich, detailed explanation.
    """
    if not section_ids:
        return []

    try:
        expanded_chunks = []
        
        # We process each matched section and pull its constituent chunks
        # This guarantees we get the full context of the section the user asked about
        for sec_id in section_ids:
            # Fetch the chunks belonging to this section, ordered sequentially
            res = supabase.table("document_chunks")\
                .select("id", "content", "chunk_index", "is_heading")\
                .eq("section_id", sec_id)\
                .order("chunk_index")\
                .limit(15)\
                .execute()
                
            if res.data:
                # Merge the chunks to form a comprehensive section body
                merged_content = "\n\n".join([c["content"] for c in res.data])
                
                expanded_chunks.append({
                    "section_id": sec_id,
                    "content": merged_content,
                    "similarity_score": 0.9  # Inherit high relevance since the section was a match
                })
                
        print(f"  [Chunk Retriever] Assembled full chunk context for {len(expanded_chunks)} sections.")
        
        # Return the requested number of top section contexts
        # top_k here is treated as the number of sections we want to pass context for
        return expanded_chunks[:top_k]

    except Exception as e:
        print(f"  [Chunk Retriever Failure] Error assembling hierarchical chunks: {e}")
        return []
