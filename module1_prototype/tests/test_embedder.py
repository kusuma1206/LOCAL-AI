import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from processing.embedder import generate_embeddings

def test_embedder():
    print("Running Embedder Tests...")
    
    chunks = ["This is a test chunk.", "Another piece of text."]
    
    try:
        embeddings = generate_embeddings(chunks)
        print(f"Number of embeddings: {len(embeddings)}")
        print(f"Embedding dimension: {len(embeddings[0])}")
        
        assert len(embeddings) == 2
        assert len(embeddings[0]) == 384 # Dim for all-MiniLM-L6-v2
        
        print("Embedder tests passed successfully.")
    except Exception as e:
        print(f"Embedder test failed: {e}")

if __name__ == "__main__":
    test_embedder()
