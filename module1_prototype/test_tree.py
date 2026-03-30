import sys
sys.path.append('.')
from processing.structure_analyzer import build_section_tree

lines = [
    "Intro text before header.",
    "# Document",
    "## Overview",
    "This is the overview.",
    "## Architecture",
    "### Layer 1",
    "#### Threshold Logic",
    "Logic details.",
    "### Layer 2",
    "Layer 2 details."
]

sections = build_section_tree(lines, 123)

for s in sections:
    parent = s['parent_section_id']
    print(f"Level {s['level']} | Order {s['section_order']} | {s['title']} (Parent: {str(parent)[:8] if parent else 'None'})")
    if s['content']:
        print(f"  Snippet: {s['content'][:30]}")
