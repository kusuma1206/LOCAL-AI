from supabase import create_client, Client
import os
from dotenv import load_dotenv
from retrieval import mode_router

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def test_debug():
    query = "What is the Similarity Gate in Zero Trust AI architecture?"
    print(f"Testing Debug Output for Query: {query}")
    
    # This should trigger the debug prints inside chunk_retriever.py
    # and the full expansion in mode_router.py
    res = mode_router.handle_query(supabase, query, mode="explain")
    
    print("\n--- Response ---")
    # print(res["formatted_answer"][:500] if isinstance(res, dict) else res)

if __name__ == "__main__":
    test_debug()
