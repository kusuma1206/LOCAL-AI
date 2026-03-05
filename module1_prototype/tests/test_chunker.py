import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from processing.chunker import chunk_text

def test_chunker():
    print("Running Chunker Tests...")
    
    # Test 1: Basic chunking
    text = "ABCDEFGHIJ" # 10 chars
    # Size 4, Overlap 2
    # 1: ABCD (start 0, end 4)
    # 2: CDEF (start 2, end 6)
    # 3: EFGH (start 4, end 8)
    # 4: GHIJ (start 6, end 10)
    # 5: IJ (start 8, end 12) -> wait, start += 2. 0,2,4,6,8. 
    chunks = chunk_text(text, chunk_size=4, overlap=2)
    print(f"Chunks: {chunks}")
    assert chunks == ["ABCD", "CDEF", "EFGH", "GHIJ", "IJ"]
    
    # Test 2: Text shorter than chunk size
    text = "Hello"
    chunks = chunk_text(text, chunk_size=10, overlap=2)
    print(f"Short text: {chunks}")
    assert chunks == ["Hello"]
    
    # Test 3: Large text
    text = "A" * 1000
    chunks = chunk_text(text, chunk_size=500, overlap=50)
    print(f"Large text chunks: {len(chunks)}")
    assert len(chunks) > 1
    
    print("Chunker tests passed successfully.")

if __name__ == "__main__":
    test_chunker()
