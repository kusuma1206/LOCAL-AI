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

def detect_query_intent(query: str) -> str:
    """
    Detects whether the user is asking for a document overview or a specific topic.
    Returns: 'overview' or 'specific'
    """
    query_lower = query.lower().strip()
    
    # 1. Patterns that almost always indicate a SPECIFIC technical question
    specific_patterns = [
        "what is", "how does", "verify", "check", "where is", "who is",
        "tell me about the", "details of", "function of", "purpose of",
        "how can i", "is there", "list the"
    ]
    
    # If it starts with or clearly contains a specific question pattern, route to 'specific'
    if any(query_lower.startswith(p) or f" {p} " in f" {query_lower} " for p in specific_patterns):
        # Exception: "What is this document" or "What is the overview"
        if not any(kw in query_lower for kw in ["this document", "overview", "summary"]):
            return "specific"

    # 2. Keywords that indicate a broad OVERVIEW or EXPLANATION
    overview_keywords = [
        "overview", "summarize", "describe", 
        "explain architecture", "explain document", "full explanation",
        "explain zero trust", "explain document", "about the document", 
        "summary of"
    ]
    
    # 3. Breadth check: "Explain [System]" usually wants an overview
    if "explain" in query_lower and not any(p in query_lower for p in ["how to", "specifically", "the code for"]):
        if any(kw in query_lower for kw in ["architecture", "system", "design", "workflow", "process"]):
            return "overview"

    if any(kw in query_lower for kw in overview_keywords):
        return "overview"
    
    return "specific"

def handle_query(supabase, query: str, mode: str = "id_only", chat_history: list[dict] = None, diagnostic: bool = True) -> any:
    """
    Hierarchical Retrieval Router: Orchestrates query embedding and multi-stage retrieval.
    Includes full-pipeline latency measurement for all 8 stages.
    """
    import time
    from . import diagnostics
    
    if diagnostic:
        diagnostics.log_step_1_query(query)
    
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
    primary_filename = "Unknown"

    try:
        validation = guardrail_engine.validate_input(query)
        latencies["guardrails_check"] = time.time() - t_start_gr

        if validation["status"] == "BLOCKED":
            results = validation["reason"]
            return results

        # 2. Intent-Based Routing
        q_intent = detect_query_intent(query)
        if q_intent == "overview":
            print(f"  [Mode Router] Overview mode activated via query intent")
            mode = "overview_mode"
        elif q_intent == "specific" and mode != "id_only":
            print(f"  [Mode Router] Specific mode activated via query intent")
            mode = "technical"
        
        # 3. Heavy Module Imports
        from . import query_embedder, document_retriever, section_retriever, chunk_retriever, response_formatter, slm_generator
        import response_formatter as final_formatter
        
        t_start_embed = time.time()
        query_embedding = query_embedder.generate_query_embedding(query)
        latencies["embedding"] = time.time() - t_start_embed
        
        if diagnostic:
            diagnostics.log_step_2_embedding(query_embedding)

        if not query_embedding:
            return "Not Found"
            
        # 4.5 Retrieve Top Documents
        t_start_doc = time.time()
        top_chunks_raw = []
        
        if mode in ["overview_mode", "explain"]:
            # --- TOP-DOWN FLOW ---
            print(f"  [Mode Router] Using TOP-DOWN (Weighted Voting) for <{mode}>...")
            scored_doc_id = document_retriever.get_top_document(supabase, query_embedding)
            if scored_doc_id:
                try:
                    res = supabase.table("documents").select("filename, title, storage_url").eq("doc_id", scored_doc_id).execute()
                    primary_doc_id = scored_doc_id
                    primary_filename = res.data[0]["filename"] if res.data else "Unknown"
                    storage_url = res.data[0]["storage_url"] if res.data else None
                except:
                    primary_doc_id = scored_doc_id
                    primary_filename = "Unknown"
                    storage_url = None
                doc_ids = [primary_doc_id]
            else:
                return "Information not found in the documents."
        else:
            # --- BOTTOM-UP FLOW ---
            print(f"  [Mode Router] Using BOTTOM-UP (Chunk-First) for <{mode}>...")
            from processing.storage import search_chunks
            
            # SAFEGUARD: For specific technical queries, we only want the absolute best match
            # to avoid cross-section contamination.
            search_k = 1 if mode == "technical" else 8
            top_chunks_raw = search_chunks(supabase, query_embedding, top_k=search_k)
            if not top_chunks_raw:
                return "Information not found in the documents."
            
            sec_ids = list(set([c["section_id"] for c in top_chunks_raw if c.get("section_id")]))
            doc_res = supabase.table("sections").select("document_id").in_("section_id", sec_ids).execute()
            doc_ids = list(set([r["document_id"] for r in doc_res.data])) if doc_res.data else []
            primary_doc_id = doc_ids[0] if doc_ids else None
            
        latencies["document_retrieval"] = time.time() - t_start_doc
        
        if diagnostic:
            diagnostics.log_step_5_mode(mode if mode else q_intent)

        # 4.6 Hierarchical Mapping & Guardrails
        t_start_sec = time.time()
        section_ids = []
        top_chunks = []
        top_sections = [] 
        
        if mode in ["overview_mode", "explain"]:
            res_s = supabase.table("sections").select("section_id, title, section_summary").eq("document_id", primary_doc_id).execute()
            section_ids = [s["section_id"] for s in res_s.data] if res_s.data else []
            top_sections = [{"similarity_score": 1.0, "section_id": sid, "section_summary": s.get("section_summary", "No summary")} for s, sid in zip(res_s.data, section_ids)]
        else:
            top_chunks = top_chunks_raw
            # Only use the section of the single best chunk if technical mode
            if mode == "technical" and top_chunks:
                section_ids = [top_chunks[0]["section_id"]] if top_chunks[0].get("section_id") else []
            else:
                section_ids = list(set([c["section_id"] for c in top_chunks if c.get("section_id")]))

            if section_ids:
                res_s = supabase.table("sections").select("section_id, title, document_id").in_("section_id", section_ids).execute()
                top_sections = [{"similarity_score": 0.8, "section_id": s["section_id"]} for s in res_s.data] if res_s.data else []
                if res_s.data and primary_filename == "Unknown":
                    try:
                        res_d = supabase.table("documents").select("filename, storage_url").eq("doc_id", res_s.data[0]["document_id"]).execute()
                        if res_d.data: 
                            primary_filename = res_d.data[0]["filename"]
                            storage_url = res_d.data[0]["storage_url"]
                    except: pass
        latencies["section_retrieval"] = time.time() - t_start_sec
            
        relevance_score = top_sections[0].get("similarity_score", 0) if top_sections else (top_chunks[0].get("similarity_score", 0) if top_chunks else 0)
        domain_ok = guardrail_engine.check_domain_relevance(relevance_score)
        if not domain_ok:
            return "Information not found in the documents."

        # 6. Chunk Retrieval
        t_start_chunk = time.time()
        if mode != "id_only" and not top_chunks:
            top_k_chunks = 12 if mode == "explain" else 5
            top_chunks = chunk_retriever.retrieve_top_chunks(supabase, query_embedding, section_ids, top_k=top_k_chunks, query=query)
            
        chunk_ids = [c.get("id") for c in top_chunks] 
        chunk_scores = {str(c.get("id", i)): c.get("similarity_score", 0) for i, c in enumerate(top_chunks)}
        if diagnostic:
            diagnostics.log_step_3_chunks(top_chunks)
            diagnostics.log_step_4_coverage(top_chunks)
        latencies["chunk_retrieval"] = time.time() - t_start_chunk

        # 8. Mode Routing & Context Preparation
        t_start_ctx = time.time()
        final_context = []
        sections_for_format = []
        
        if mode in ["overview_mode", "explain"]:
            # Context for Top-Down
            try:
                res_doc = supabase.table("documents").select("document_summary").eq("doc_id", primary_doc_id).execute()
                if res_doc.data:
                    final_context.append({"type": "global_summary", "content": res_doc.data[0]['document_summary']})
            except: pass
            for s in top_sections:
                final_context.append({"type": "section_summary", "title": s.get("title"), "content": s.get("section_summary")})
            
            # Expansion for Format
            print(f"  [Mode Router] Expanding full document {primary_doc_id} for <{mode}>")
            full_doc_text = document_retriever.retrieve_document_sections(supabase, primary_doc_id)
            if full_doc_text:
                sections_for_format.append({
                    "section_name": "Comprehensive Document Analysis",
                    "document_name": primary_filename,
                    "document_id": primary_doc_id,
                    "similarity_score": 1.0,
                    "content_text": full_doc_text
                })
        else:
            # Context and Formatting for Bottom-Up
            for c in top_chunks:
                final_context.append({"type": "chunk", "content": c.get('content', '')})
                # Auto-fetch titles if missing
                sec_title = "Technical Detail"
                if c.get("section_id"):
                    try:
                        res_s = supabase.table("sections").select("title").eq("section_id", c["section_id"]).execute()
                        if res_s.data: sec_title = res_s.data[0]["title"]
                    except: pass
                sections_for_format.append({
                    "section_name": sec_title,
                    "document_name": primary_filename or "Unknown",
                    "document_id": primary_doc_id or "Unknown",
                    "similarity_score": c.get("similarity_score", 0.0),
                    "content_text": c.get("content", "")
                })

        latencies["context_preparation"] = time.time() - t_start_ctx
        
        # 9. Response Generation
        formatted_answer = "No sections to format."
        if sections_for_format:
            if mode == "explain":
                # Use high-fidelity SLM generation for explanations
                context_texts = [s["content_text"] for s in sections_for_format]
                slm_response, slm_latencies = slm_generator.generate_explanation(
                    query, 
                    context_texts, 
                    chat_history=history
                )
                # Apply final structural formatting passthrough
                formatted_answer = final_formatter.format_response(slm_response)
                latencies.update(slm_latencies)
            else:
                raw_formatted = response_formatter.format_conversational_response(query, sections_for_format)
                # Final Pass: Advanced Structural Formatting
                formatted_answer = final_formatter.format_response(raw_formatted)
            
            if diagnostic:
                diagnostics.log_step_8_assembly(formatted_answer, len(top_chunks), [s['section_name'] for s in sections_for_format])
            
            # Append shareable link (High-Premium UX)
            if storage_url:
                formatted_answer += f"\n\n---\n### 📄 [View Original Document]({storage_url})\n"
        
        results = {
            "intent": intent, "mode": mode,
            "primary_doc_id": primary_doc_id, 
            "primary_filename": primary_filename,
            "storage_url": storage_url if 'storage_url' in locals() else None,
            "retrieved_context": final_context, "formatted_answer": formatted_answer,
            "metadata": {"num_sections": len(top_sections), "num_chunks": len(top_chunks), "latencies": latencies}
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
