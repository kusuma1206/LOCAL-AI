import sys
import os

# Ensure the module can be imported
sys.path.append(os.path.abspath('.'))

from retrieval import mode_router
from processing import storage

def test_latency_report():
    query = "overview of the project"
    mode = "explain"
    
    print(f"--- Running Latency Verification ---")
    print(f"Query: {query} | Mode: {mode}")
    
    # Run the query. The report should print to console.
    result = mode_router.handle_query(storage.supabase, query, mode)
    
    print("\n--- Final Result Snippet ---")
    print(str(result)[:200] + "...")

if __name__ == "__main__":
    test_latency_report()
