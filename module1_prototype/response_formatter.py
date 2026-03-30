import re
import textwrap
from tabulate import tabulate
from markdown_it import MarkdownIt

def format_table(data: list) -> str:
    """
    Converts structured lists into a GitHub-flavored Markdown table.
    Automatically generates headers if not provided.
    """
    if not data:
        return ""
    
    # Auto-generate headers if the first row doesn't look like headers
    # (Simple heuristic: if only 1 row, or if we want to be safe)
    headers = "firstrow"
    if len(data) == 1:
        headers = [f"Column {i+1}" for i in range(len(data[0]))]
    
    return tabulate(data, headers=headers, tablefmt="github")

def format_lists(text: str) -> str:
    """
    Detects step-based explanations and converts them into properly formatted Markdown lists.
    Handles both numbered (1., 2.) and bullet points (-, *, •).
    """
    lines = text.split('\n')
    formatted_lines = []
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            formatted_lines.append("")
            continue
            
        # Detect Numbered Steps / Sequences
        step_match = re.match(r'^(\d+)[.)]\s+(.*)', stripped)
        if step_match:
            formatted_lines.append(f"{step_match.group(1)}. {step_match.group(2)}")
            continue

        # Detect Bullet Points
        bullet_match = re.match(r'^([*\-•+])\s+(.*)', stripped)
        if bullet_match:
            formatted_lines.append(f"- {bullet_match.group(2)}")
            continue
            
        formatted_lines.append(line)
        
    return "\n".join(formatted_lines)

def render_markdown(markdown_text: str) -> str:
    """
    Parses and validates the final Markdown, returning clean HTML-safe output.
    Uses the markdown-it-py parser.
    """
    if not markdown_text:
        return ""
    
    return md.render(markdown_text)

def format_response(text: str) -> str:
    """
    Improves the structure and formatting of RAG responses without modifying semantic content.
    Detects lists, numbered steps, tables, and headings.
    """
    if not text:
        return ""

    # 1. High-Precision Normalization (V4.1 Rules)
    # Normalize all bullet markers to '- '
    text = re.sub(r'^[*\-•+]\s+', '- ', text, flags=re.MULTILINE)
    
    # NEW: Force "ACTIVITY LOG FOR WEEK" to start on a new line with its own paragraph
    text = re.sub(r'(?<!\n\n)(ACTIVITY LOG FOR WEEK)', r'\n\n\1', text)
    
    # Ensure bullets start on new lines
    text = re.sub(r'(?<!\n)- ', '\n- ', text)
    
    # Ensure numbered lists start on new lines
    text = re.sub(r'(?<!\n)(\d+)\.\s+', r'\n\1. ', text)
    
    # NEW: Detect and fix numbers starting a sentence after "WEEK X Topic"
    # We force a double newline before the activity number to create a new paragraph
    text = re.sub(r'(Topic:.*?WEEK)\s+(\d+)\s+', r'\1\n\n- \2 ', text, flags=re.IGNORECASE)

    # AGGRESSIVE LABEL MERGING: Join labels and descriptions even if split or bulleted.
    # Pattern: Optional Bullet -> Optional Bold -> Label -> Colon -> Optional Bold -> Optional Newline -> Explanation
    labels = ["File", "Persona", "Constraint", "Fallback", "Algorithm", "Process", "Logging", "Output", "Configuration", "Threshold", "Latency"]
    label_pattern = "|".join(labels)
    
    # 1. Join split lines for labels (e.g., - **Label**:\n - Explanation)
    # This handles both bulleted and non-bulleted labels split across lines.
    # We optionally strip leading bullets from the explanation line too.
    text = re.sub(rf'^(?:-\s+|\*\s+)?\**\s*({label_pattern})\s*:?\**\s*\n\s*(?:[*\-•+]\s+)?(.+)', r'**\1:** \2', text, flags=re.MULTILINE | re.IGNORECASE)
    
    # 2. Enforce standard formatting for inline labels (e.g., * Algorithm: Explanation)
    text = re.sub(rf'^(?:-\s+|\*\s+)?\**\s*({label_pattern})\s*:\s*(.+)', r'**\1:** \2', text, flags=re.MULTILINE | re.IGNORECASE)

    # 3. Handle double-bulleted results from poor merging
    text = re.sub(r'^- - ', '- ', text, flags=re.MULTILINE)

    # Normalize spacing: collapse multiple newlines, trim lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # 2. Existing formatting logic
    text = format_lists(text)
    
    lines = [line.strip() for line in text.split('\n')]

    formatted_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Skip empty lines
        if not line:
            if not formatted_lines or formatted_lines[-1] != "":
                formatted_lines.append("")
            i += 1
            continue

        # 3. Detect Tables (Pseudo-tables like | col 1 | col 2 |)
        if '|' in line:
            table_data = []
            while i < len(lines) and '|' in lines[i]:
                row_line = lines[i]
                # Extract cells, keeping raw content for now
                cells = [cell.strip() for cell in row_line.split('|')]
                # Remove empty edge cells if they exist (common in | a | b |)
                if cells and not cells[0]: cells = cells[1:]
                if cells and not cells[-1]: cells = cells[:-1]
                
                # Filter out separator rows (|---|) from data matrix
                if not all(re.match(r'^[\s\-:]+$', c) for c in cells):
                    table_data.append(cells)
                i += 1
            
            if table_data:
                formatted_lines.append(format_table(table_data))
                formatted_lines.append("") # Spacing after table
            continue

        # 4. Detect Numbered Steps / Sequences 
        if re.match(r'^\d+\.\s+', line):
            formatted_lines.append(line)
            i += 1
            continue

        # 5. Detect Bullet Points 
        if re.match(r'^\-\s+', line):
            formatted_lines.append(line)
            i += 1
            continue

        # 6. Detect Headings
        if i + 1 < len(lines) and len(lines[i+1]) > 3 and all(c == '=' for c in lines[i+1]):
            formatted_lines.append(f"# {line}")
            i += 2
            continue
        if i + 1 < len(lines) and len(lines[i+1]) > 3 and all(c == '-' for c in lines[i+1]):
            formatted_lines.append(f"## {line}")
            i += 2
            continue
        
        # 7. Paragraph Handling (Stop manual wrapping, let frontend handle it)
        if line:
            formatted_lines.append(line)
        
        i += 1

    return "\n".join(formatted_lines).strip()

# Initialize Markdown parser for potential future safety checks or rendering
md = MarkdownIt()

if __name__ == "__main__":
    # Test 1: format_response with messy text
    print("--- Test 1: format_response ---")
    sample_text = """
    User Manual
    ===========
    
    Getting Started
    ---------------
    1. plug in the device
    2. Turn on the power switch
    * Ensure the battery is charged.
    * Check the indicator light.
    
    Data Specifications:
    | ID | Name | Status |
    |---|---|---|
    | 1 | Sensor A | Active |
    | 2 | Sensor B | Idle |
    
    This is a very long paragraph that needs to be wrapped correctly for better readability in the final output and should not be modified semantically at all.
    """
    print(format_response(sample_text))

    # Test 2: format_table with raw data
    print("\n--- Test 2: format_table (No Headers) ---")
    raw_data = [
        ["Sensor A", "Active", "Normal"],
        ["Sensor B", "Idle", "Warning"]
    ]
    print(format_table(raw_data))

    # Test 3: format_lists with step-based text
    print("\n--- Test 3: format_lists ---")
    list_text = """
    1) Step one: do this
    2. Step two: then that
    * Feature A
    • Feature B
    - Feature C
    """
    print(format_lists(list_text))

    # Test 4: render_markdown (HTML Output)
    print("\n--- Test 4: render_markdown (HTML) ---")
    md_text = "# Heading\n- Item 1\n- Item 2"
    print(render_markdown(md_text))
