def retrieve_top_documents(supabase, query_embedding: list, top_k: int = 3) -> list:
    """
    Retrieves the most similar documents using the 'match_documents' RPC.
    """
    if not query_embedding:
        return []

    try:
        response = supabase.rpc("match_documents", {
            "query_embedding": query_embedding,
            "match_count": top_k
        }).execute()

        if not response.data:
            print("  [Document Retriever Warning] No similar documents found.")
            return []

        top_docs = []
        for row in response.data:
            top_docs.append({
                "doc_id": row.get("doc_id"),
                "filename": row.get("filename"),
                "summary": row.get("document_summary"),
                "similarity_score": row.get("similarity")
            })

        print(f"  [Document Retriever] Found {len(top_docs)} relevant documents.")
        return top_docs

    except Exception as e:
        print(f"  [Document Retriever Failure] Error during document matching: {e}")
        return []
