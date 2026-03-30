import sys
sys.path.append('.')
from retrieval.query_embedder import generate_query_embedding
from processing.storage import search_chunks, supabase

query = "What is Similarity Gate?"
print(f"Embedding query: '{query}'")
qe = generate_query_embedding(query)

print("Searching vector space...")
results = search_chunks(supabase, qe, top_k=2)

if not results:
    print("No results returned.")
else:
    for idx, r in enumerate(results):
        print(f"\nResult {idx+1}:")
        print(f"  Chunk ID: {r['chunk_id']}")
        print(f"  Section ID: {r['section_id']}")
        print(f"  Score: {r['similarity_score']:.4f}")
        print(f"  Content snippet: {r['content'][:100]}...")
