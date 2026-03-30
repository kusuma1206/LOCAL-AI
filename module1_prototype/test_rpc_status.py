from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def test_rpc():
    try:
        print("Testing match_documents RPC...")
        # Dummy embedding (all zeros)
        dummy_emb = [0.0] * 384
        res = supabase.rpc("match_documents", {
            "query_embedding": dummy_emb,
            "match_count": 1
        }).execute()
        print("RPC Result Status: Success" if res.data is not None else "RPC Result Status: No Error but No Data")
        if res.data:
            print(f"Sample data from RPC: {res.data[0]}")
    except Exception as e:
        print(f"RPC Failed: {e}")

if __name__ == "__main__":
    test_rpc()
