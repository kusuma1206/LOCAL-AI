import sys
from processing.structure_analyzer import detect_heading

tests = [
    "### Layer 1: Similarity Gate",
    "# Heading",
    "## Subheading",
    "Not a heading",
    "  #  Bad formatting",
    "#### "
]

for t in tests:
    print(f"'{t}' -> {detect_heading(t)}")
