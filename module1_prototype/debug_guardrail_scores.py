import sys
from retrieval import query_embedder, section_retriever
from processing.storage import supabase

def debug_query_scores(query: str):
    print(f"\n--- Debugging Similarity Scores for: '{query}' ---")
    
    from retrieval.guardrails import guardrail_engine
    val = guardrail_engine.validate_input(query)
    if val["status"] == "BLOCKED":
        print(f"BLOCK: Pre-check blocked this query: {val['reason']}")
        # We continue to see scores anyway for debug
    
    # 1. Embed the query
    embedding = query_embedder.embed_query(query)
    
    # 2. Retrieve sections with scores
    sections = section_retriever.retrieve_top_sections(supabase, embedding, top_n=5)
    
    with open("debug_scores.txt", "w") as f:
        f.write(f"Query: {query}\n")
        from retrieval.guardrails import guardrail_engine
        val = guardrail_engine.validate_input(query)
        if val["status"] == "BLOCKED":
            f.write(f"PRE-CHECK: BLOCKED - {val['reason']}\n")
        else:
            f.write("PRE-CHECK: PASSED\n")

        f.write(f"Top 5 Sections:\n")
        for i, s in enumerate(sections):
            f.write(f"  [{i}] Title: {s.get('section_title')} | Score: {s.get('similarity_score')}\n")
        
        top_score = sections[0].get('similarity_score', 0)
        f.write(f"\nTop Score: {top_score}\n")
        if guardrail_engine.check_domain_relevance(top_score):
            f.write("DOMAIN CHECK: PASSED\n")
            f.write("RESULT: Passes to SLM\n")
        else:
            f.write("DOMAIN CHECK: BLOCKED\n")
            f.write("RESULT: Should be BLOCKED\n")
    print("Debug scores written to debug_scores.txt")

if __name__ == "__main__":
    query = "How to cook pasta?"
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    debug_query_scores(query)
