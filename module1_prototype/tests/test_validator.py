import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from processing.validator import validate_document

def test_validator():
    test_cases = [
        ("test.pdf", False),     # Non-existent
        ("main.py", False),      # Wrong extension
        ("README.md", True),     # (If exists and valid)
    ]
    
    # Create a dummy md file for testing
    with open("dummy.md", "w") as f:
        f.write("# Dummy file")
    
    print("Running Validator Tests...")
    
    # Test 1: Unsupported extension
    res, msg = validate_document("main.py")
    print(f"main.py (invalid ext): {res} - {msg}")
    
    # Test 2: Valid extension
    res, msg = validate_document("dummy.md")
    print(f"dummy.md (valid): {res} - {msg}")
    
    # Test 3: Non-existent
    res, msg = validate_document("non_existent.pdf")
    print(f"non_existent.pdf: {res} - {msg}")
    
    os.remove("dummy.md")

if __name__ == "__main__":
    test_validator()
