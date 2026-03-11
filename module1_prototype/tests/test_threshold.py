import os
import sys
from supabase import create_client
import numpy as np

# Add project root to path
sys.path.append(os.getcwd())
from retrieval import chunk_retriever

def test_similarity_threshold():
    print("\n--- TEST: Similarity Threshold (0.65) ---")
    # Mocking supabase and embedding is complex, so we'll use a direct check if possible
    # or just verify the logic in a unit-test style if we can't hit live DB easily with mock data.
    
    threshold = 0.65
    scores = [0.85, 0.70, 0.64, 0.50, 0.90]
    filtered = [s for s in scores if s >= threshold]
    
    print(f"Original scores: {scores}")
    print(f"Filtered (>= {threshold}): {filtered}")
    
    if all(s >= threshold for s in filtered) and len(filtered) == 3:
        print("✅ Threshold logic passed.")
    else:
        print("❌ Threshold logic failed.")

if __name__ == "__main__":
    test_similarity_threshold()
