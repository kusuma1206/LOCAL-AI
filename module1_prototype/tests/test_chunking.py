import os
import sys

# Add project root to path
sys.path.append(os.getcwd())
from processing import chunker

def test_section_chunking():
    print("\n--- TEST: Section-Based Chunking ---")
    sections = [
        {"section_title": "Layer 1", "content": "This is layer 1 content."},
        {"section_title": "Layer 2", "content": "This is layer 2 content which is a bit longer."},
        {"section_title": "Empty Layer", "content": ""}
    ]
    
    chunks = chunker.chunk_text(sections, chunk_size=100)
    
    print(f"Input sections: {len(sections)}")
    print(f"Output chunks: {len(chunks)}")
    
    for i, c in enumerate(chunks):
        print(f"Chunk {i+1} title: {c['section_title']}")
        print(f"Chunk {i+1} text: {c['chunk_text']}\n")
    
    if len(chunks) == 2 and chunks[0]['section_title'] == "Layer 1":
        print("✅ Section chunking logic passed.")
    else:
        print("❌ Section chunking logic failed.")

if __name__ == "__main__":
    test_section_chunking()
