import sys
import os
sys.path.append(os.getcwd())

from retrieval.mode_router import handle_query
from processing.storage import supabase

query = "explain zero trust ai archietcture"
print(f"Testing Query: {query}")

res = handle_query(supabase, query)

print("\n--- FINAL RESULT ---")
if isinstance(res, dict):
    print("Mode:", res.get('mode'))
    print("Primary Doc ID:", res.get('primary_doc_id'))
    print("Formatted Answer Snippet:", res.get('formatted_answer', '')[:200])
else:
    print("Result (String):", res)
