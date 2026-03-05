import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from processing.cleaner import clean_text

def test_cleaner():
    print("Running Cleaner Tests...")
    
    # Test 1: Multiple spaces
    input_text = "This  is   a    test."
    cleaned = clean_text(input_text)
    print(f"Spaces: '{input_text}' -> '{cleaned}'")
    assert cleaned == "This is a test."
    
    # Test 2: Excessive line breaks
    input_text = "Para 1\n\n\n\nPara 2"
    cleaned = clean_text(input_text)
    print(f"Newlines: 'Para 1\\n\\n\\n\\nPara 2' -> 'Para 1\\n\\nPara 2'")
    assert cleaned == "Para 1\n\nPara 2"
    
    # Test 3: Stripping
    input_text = "  Trim me  "
    cleaned = clean_text(input_text)
    print(f"Stripping: '{input_text}' -> '{cleaned}'")
    assert cleaned == "Trim me"
    
    print("Cleaner tests passed successfully.")

if __name__ == "__main__":
    test_cleaner()
