import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from processing.extractor import extract_text

def test_extractor():
    # Create a dummy md file
    test_md = "test_extract.md"
    with open(test_md, "w", encoding='utf-8') as f:
        f.write("# Hello\nThis is a test.")
    
    try:
        print("Testing Markdown extraction...")
        text = extract_text(test_md)
        print(f"Extracted text:\n{text}")
        assert "Hello" in text
        print("Markdown extraction successful.")
        
        # We won't test PDF/DOCX here as generating binary files is complex without tools
        # but the logic is implemented using the libraries.
        
    finally:
        if os.path.exists(test_md):
            os.remove(test_md)

if __name__ == "__main__":
    test_extractor()
