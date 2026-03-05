from processing import storage
from retrieval import query_embedder

query = 'Production Deployment'
emb = query_embedder.embed_query(query)
res = storage.supabase.rpc('match_sections', {
    'query_embedding': emb, 
    'match_count': 5
}).execute()

print("--- SIMILARITY SCORES ---")
if not res.data:
    print("No data found.")
else:
    for r in res.data:
        print(f"Doc: {r.get('document_id')} | Score: {r.get('similarity'):.4f} | Section: {r.get('section_title')}")
