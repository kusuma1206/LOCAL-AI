import sys
import os

# No need to add path if we are running in the project dir or if we use relative imports
from processing.structure_analyzer import analyze_structure

def test_fallback_segmentation():
    # Create a long text with no headings (~2500 characters)
    sentence = "This is a long sentence that repeats to create a large unstructured block of text. "
    text = sentence * 30
    
    print(f"Testing with text of length: {len(text)}")
    
    sections = analyze_structure(text)
    
    print(f"\nDetected {len(sections)} sections.")
    for i, s in enumerate(sections):
        content_len = len(s['content'])
        print(f"[{i+1}] {s['section_title']} - Length: {content_len}")
        # Check if it doesn't break mid-sentence (should end with '.')
        if not s['content'].endswith('.'):
             print(f"  WARNING: Section {i+1} does not end with a sentence boundary!")

    # Assertions
    assert len(sections) > 1, "Should have created multiple sections"
    assert sections[0]['section_title'] == "Section 1", "First section title mismatch"
    for s in sections:
        assert len(s['content']) >= 300 or len(sections) == 1, f"Section {s['section_title']} is too short: {len(s['content'])}"

def test_no_fallback_for_short_text():
    text = "Short text without headings."
    sections = analyze_structure(text)
    assert len(sections) == 1
    assert sections[0]['section_title'] == "Initial Segment"
    print("\nShort text test passed (no fallback).")

def test_no_fallback_with_headings():
    text = "# Heading 1\nSome content here.\n# Heading 2\nMore content here."
    sections = analyze_structure(text)
    assert len(sections) == 2
    assert sections[0]['section_title'] == "Heading 1"
    print("\nHeading text test passed (no fallback).")

if __name__ == "__main__":
    try:
        test_fallback_segmentation()
        test_no_fallback_for_short_text()
        test_no_fallback_with_headings()
        print("\nAll tests passed successfully!")
    except Exception as e:
        print(f"\nTest failed: {e}")
        sys.exit(1)
