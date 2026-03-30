from retrieval import mode_router
from processing.storage import supabase
import json

query = "What is the Similarity Gate in Zero Trust AI architecture?"
mode = "technical"

print(f"Testing query: {query} with mode: {mode}")
try:
    result = mode_router.handle_query(supabase, query, mode)
    print("Result retrieved successfully!")
    print(json.dumps(result, indent=2))
except Exception as e:
    import traceback
    print("FAILED with exception:")
    traceback.print_exc()
