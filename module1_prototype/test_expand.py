import sys
sys.path.append('.')
from processing.storage import search_chunks, supabase, expand_section
from retrieval.query_embedder import generate_query_embedding

qe = generate_query_embedding("What is Similarity Gate?")
results = search_chunks(supabase, qe, top_k=1)

if results:
    section_id = results[0]["section_id"]
    print(f"\n1. Found matching chunk from Section ID: {section_id}")
    
    print("\n2. Expanding full section...")
    full_text = expand_section(section_id)
    
    print("\n--- EXTRACTED FULL SECTION TEXT ---")
    print(full_text)
    print("-----------------------------------")
    print(f"Total characters: {len(full_text)}")
else:
    print("No chunks found.")
