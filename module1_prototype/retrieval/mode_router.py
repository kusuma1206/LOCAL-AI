import time
from .guardrails import guardrail_engine

def detect_intent(query: str) -> str:
    """
    Classifies the user query into GREETING, OUT_OF_SCOPE, or TECHNICAL.
    """
    query_lower = query.lower().strip()
    
    # 1. Greetings
    greetings = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening", "howdy"]
    if any(query_lower == g or query_lower.startswith(g + " ") or query_lower.startswith(g + "!") for g in greetings):
        return "GREETING"
    
    # 2. Out of Scope (Heuristic-based)
    out_of_scope_keywords = ["joke", "weather", "news", "sport", "game", "movie", "song", "recipe", "who is", "what is the capital"]
    # We allow "what is" if it follows with technical terms, but here we keep it simple for now.
    # A better approach is to check if it's a very short query that isn't technical.
    
    # 3. Technical (Default)
    return "TECHNICAL"

def handle_query(supabase, query: str, mode: str = "id_only", chat_history: list[dict] = None) -> any:
    """
    Hierarchical Retrieval Router: Orchestrates query embedding and multi-stage retrieval.
    Includes full-pipeline latency measurement for all 8 stages.
    """
    import time
    
    # Initialize timing dictionary
    latencies = {
        "guardrails_check": 0.0,
        "embedding": 0.0,
        "document_retrieval": 0.0,
        "section_retrieval": 0.0,
        "chunk_retrieval": 0.0,
        "context_preparation": 0.0,
        "llm_generation": 0.0,
        "output_validation": 0.0
    }

    if mode != "id_only":
        print(f"\n  [Mode Router] Handling query in mode: <{mode}>")
    
    # 1. Guardrails & Intent Detection (Stage 1)
    t_start_gr = time.time()
    intent = detect_intent(query)
    
    if intent == "GREETING":
        return "Hello! I am your SLM Technical Mentor. How can I assist you with your technical documents today?"
    
    # Use a flag to ensure we don't print report for greetings or non-technical starts
    results = "Not Found"
    section_ids = []
    chunk_ids = []
    section_scores = {}
    chunk_scores = {}
    primary_doc_id = None

    try:
        validation = guardrail_engine.validate_input(query)
        latencies["guardrails_check"] = time.time() - t_start_gr

        if validation["status"] == "BLOCKED":
            results = validation["reason"]
            return results

        # 2. Intent-Based Routing
        overview_keywords = ["overview", "summarize", "ideation", "project", "document"]
        if any(kw in query.lower() for kw in overview_keywords):
            print(f"  [Mode Router] Overview mode activated")
            mode = "overview_mode"
        
        # 3. Heavy Module Imports
        from . import query_embedder, document_retriever, section_retriever, chunk_retriever
        
        # 4. Embed Query (Stage 2)
        t_start_embed = time.time()
        query_embedding = query_embedder.embed_query(query)
        latencies["embedding"] = time.time() - t_start_embed

        if not query_embedding:
            return "Not Found"
            
        # 4.5 Retrieve Top Documents (Stage 3 - NEW)
        t_start_doc = time.time()
        top_docs = document_retriever.retrieve_top_documents(supabase, query_embedding, top_k=3)
        latencies["document_retrieval"] = time.time() - t_start_doc
        
        if not top_docs:
            return "Information not found in the documents."
            
        doc_ids = [d["doc_id"] for d in top_docs]
        primary_doc_id = top_docs[0].get("doc_id")
        primary_filename = top_docs[0].get("filename")

        # 5. Retrieve Top Sections (Stage 4) - Filtered by Doc IDs
        t_start_sec = time.time()
        top_sections = section_retriever.retrieve_top_sections(supabase, query_embedding, top_n=5, doc_ids=doc_ids)
        latencies["section_retrieval"] = time.time() - t_start_sec

        if not top_sections:
            return "Information not found in the specific sections of the detected documents."
            
        # Domain Relevance Guardrail
        t_gr_domain_start = time.time()
        domain_ok = guardrail_engine.check_domain_relevance(top_sections[0].get("similarity_score", 0))
        latencies["guardrails_check"] += (time.time() - t_gr_domain_start)

        if not domain_ok:
            return "Information not found in the documents."
            
        # Extract IDs for chunk filtering
        section_ids = [s["section_id"] for s in top_sections]
        section_scores = {str(s["section_id"]): s["similarity_score"] for s in top_sections}
        
        # 6. Retrieve Top Chunks (Stage 5)
        t_start_chunk = time.time()
        top_chunks = []

        if mode != "id_only":
            top_k_chunks = 12 if mode == "explain" else 5
            top_chunks = chunk_retriever.retrieve_top_chunks(supabase, query_embedding, section_ids, top_k=top_k_chunks)
            chunk_ids = [c.get("id") for c in top_chunks] 
            chunk_scores = {str(c.get("id", i)): c.get("similarity_score", 0) for i, c in enumerate(top_chunks)}
        
        latencies["chunk_retrieval"] = time.time() - t_start_chunk

        # 7. Document Retrieval Details (Stage 3 Metadata)
        # (Already handled in doc_retriever)

        # 8. Mode Routing & Context Preparation
        # We no longer use SLM. We return the retrieved context/IDs directly.
        if mode == "id_only":
            results = {
                "primary_doc_id": primary_doc_id,
                "section_ids": section_ids,
                "top_sections": top_sections[:3]
            }
            
        elif mode in ["overview_mode", "explain"]:
            # Context building (Stage 6)
            t_start_ctx = time.time()
            final_context = []
            
            if mode == "overview_mode":
                all_sections_res = supabase.table("sections").select("section_title", "section_summary").eq("document_id", primary_doc_id).order("id").execute()
                if all_sections_res.data:
                    for s in all_sections_res.data:
                        final_context.append({
                            "type": "section_summary",
                            "title": s['section_title'],
                            "content": s['section_summary']
                        })
            else:
                if primary_doc_id:
                    try:
                        res_doc = supabase.table("documents").select("document_summary").eq("doc_id", primary_doc_id).execute()
                        if res_doc.data:
                            final_context.append({
                                "type": "global_summary",
                                "content": res_doc.data[0]['document_summary']
                            })
                    except: pass
                
                for s in top_sections[:5]:
                    final_context.append({
                        "type": "section",
                        "title": s.get('section_title', 'unknown'),
                        "content": s.get('section_summary', 'No summary')
                    })
                    
                for c in top_chunks:
                    final_context.append({
                        "type": "chunk",
                        "content": c.get('chunk_text', '')
                    })

            latencies["context_preparation"] = time.time() - t_start_ctx
            
            # 9. Return Structured Results
            results = {
                "intent": intent,
                "mode": mode,
                "primary_doc_id": primary_doc_id,
                "primary_filename": primary_filename,
                "retrieved_context": final_context,
                "metadata": {
                    "num_sections": len(top_sections),
                    "num_chunks": len(top_chunks),
                    "latencies": latencies
                }
            }

    finally:
        # Consolidated Latency Report (Condensed for NOLLM mode)
        if mode != "id_only":
            print(f"\n--- PERFORMANCE LATENCY REPORT ---")
            print(f"Embedding time: {latencies['embedding']:.2f}s")
            print(f"Section retrieval time: {latencies['section_retrieval']:.2f}s")
            print(f"Chunk retrieval time: {latencies['chunk_retrieval']:.2f}s")
            print(f"Total pipeline latency: {sum(latencies.values()):.2f} seconds")
            print(f"{'-'*35}\n")

    # 10. Audit Logging
    try:
        from processing import storage
        audit_scores = {"sections": section_scores, "chunks": chunk_scores}
        storage.insert_query_log(
            supabase, query, mode, section_ids, chunk_ids, audit_scores, 
            0, str(results)[:2000]
        )
    except: pass

    return results
