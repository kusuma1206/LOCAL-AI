import numpy as np

def log_step_1_query(query: str):
    print("\n" + "="*50)
    print("STEP 1 — Query Input")
    print(f"Query: \"{query}\"")
    print("="*50)

def log_step_2_embedding(embedding: list):
    print("\nSTEP 2 — Query Embedding")
    if not embedding:
        print("Query Embedding: FAILED (Empty)")
        return
    print(f"Query Embedding Length: {len(embedding)}")
    preview = [round(float(v), 4) for v in embedding[:5]]
    print(f"Embedding Preview: {preview}")

def log_step_3_chunks(chunks: list):
    print("\nSTEP 3 — Chunk Vector Search")
    print(f"Number of chunks retrieved: {len(chunks)}")
    print("\nTop Chunk Results:")
    for i, chunk in enumerate(chunks[:5]):
        print(f"\nChunk {i+1}")
        print(f"Section ID: {chunk.get('section_id')}")
        print(f"Similarity: {chunk.get('similarity_score', 0):.4f}")
        print(f"Chunk Index: {chunk.get('chunk_index', 'N/A')}")
        content = chunk.get('content', '')
        preview = content[:100].replace('\n', ' ') + "..." if len(content) > 100 else content
        print(f"Content Preview: \"{preview}\"")

def log_step_4_coverage(chunks: list):
    print("\nSTEP 4 — Section Coverage")
    if not chunks:
        print("No chunks to analyze coverage.")
        return
        
    section_ids = set([c["section_id"] for c in chunks if c.get("section_id")])
    # Note: We might not have document_id in chunk data directly anymore depending on schema
    # But we can look at what metadata is there.
    
    print(f"Unique Sections: {len(section_ids)}")
    
    # If chunks have document_name/id we use it
    doc_id_counts = {}
    for c in chunks:
        d_id = c.get("document_id")
        if d_id:
            doc_id_counts[d_id] = doc_id_counts.get(d_id, 0) + 1
            
    if doc_id_counts:
        print("Document Coverage (by chunks):")
        for d_id, count in doc_id_counts.items():
            print(f"doc_id {d_id} \u2192 {count} chunks")

def log_step_5_mode(mode: str):
    print(f"\nSTEP 5 — Mode Detection")
    print(f"Mode detected: {mode.upper()}")

def log_step_6_expansion(section_id: str, chunks: list):
    print(f"\nSTEP 6 — Section Expansion")
    print(f"Section ID: {section_id}")
    print(f"Number of chunks retrieved: {len(chunks)}")
    indices = [c.get('chunk_index') for c in chunks]
    print(f"Chunk Index Order: {indices}")
    if chunks:
        content = chunks[0].get('content', '')
        preview = content[:100].replace('\n', ' ') + "..." if len(content) > 100 else content
        print(f"Content Preview: \"{preview}\"")

def log_step_7_document_overview(doc_id: int, sections: list):
    print(f"\nSTEP 7 — Document Retrieval (Overview)")
    print(f"Selected Document ID: {doc_id}")
    print(f"Number of sections retrieved: {len(sections)}")
    titles = [s.get('section_title') or s.get('title') for s in sections]
    print(f"Section Titles: {titles}")

def log_step_8_assembly(final_response: str, chunks_used: int, section_titles: list):
    print(f"\nSTEP 8 — Final Response Assembly")
    print(f"Total characters in final response: {len(final_response)}")
    print(f"Number of chunks used: {chunks_used}")
    print(f"Section titles included: {list(set(section_titles))}")

def log_step_9_failure(reason: str):
    print(f"\nSTEP 9 — Failure Condition")
    print(f"REASON: {reason}")
    print("="*50 + "\n")
