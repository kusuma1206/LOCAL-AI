import re
import numpy as np
from sentence_transformers import SentenceTransformer, util

# Use the same model as the rest of the system
MODEL_NAME = 'all-MiniLM-L6-v2'
_model = None

def clean_markdown_noise(text: str) -> str:
    """
    Strips Mermaid diagrams, noisy headers, and redundant artifacts.
    Repairs paragraph structure and fixes Mojibake (encoding artifacts).
    """
    if not text:
        return ""

    # [MODIFIED] PRESERVING TECHNICAL ARTIFACTS
    # We no longer strip Mermaid diagrams or code blocks here as they are essential for technical documents.
    # The stripping of '#' and other noise still applies to text content, but we need to stay out of the way of blocks.
    
    # 2. Fix common Mojibake / Double-encoding artifacts
    mojibake = {
        'ΓÇó': '•',
        '≡ƒÆí': '💡',
        '≡ƒæñ': '👤',
        '≡ƒÆ¼': '💬',
        '≡ƒôé': '📂',
        'ΓÇÖ': "'",
        'ΓÇô': '-',
        'ΓÇö': '--',
        'ΓÇ£': '"',
        'ΓÇ¥': '"',
        'ΓêÜ': '✓'
    }
    for bad, good in mojibake.items():
        text = text.replace(bad, good)
    
    # [LOGIC UPDATE] We will skip aggressive stripping of '#' and code blocks if we detect they are part of a technical structure
    # However, to maintain the current 'Conversational' feel requested earlier, we still want to clean up generic noise.
    
    # 3. Strip large markdown header markers only if they aren't inside code blocks
    # (Simplified approach: only strip if line starts with # and isn't likely code)
    lines = text.split('\n')
    cleaned_lines = []
    in_code_block = False
    for line in lines:
        if line.strip().startswith('```'):
            in_code_block = not in_code_block
            cleaned_lines.append(line)
            continue
            
        if not in_code_block:
            # [MODIFIED] We no longer strip headings or bold markers 
            # as the user wants structured documentation (headings/bullets).
            pass
        
        cleaned_lines.append(line)
    text = '\n'.join(cleaned_lines)
    
    # 6. Repair broken paragraphs
    lines = text.split('\n')
    repaired_lines = []
    current_line = ""
    in_code_block = False
    
    for line in lines:
        stripped = line.strip()
        
        # Track code block state to avoid mangling technical layout
        if stripped.startswith('```'):
            if current_line:
                repaired_lines.append(current_line)
                current_line = ""
            in_code_block = not in_code_block
            repaired_lines.append(line)
            continue
            
        if in_code_block:
            repaired_lines.append(line) # Preserve exactly as is
            continue

        if not stripped:
            if current_line:
                repaired_lines.append(current_line)
                current_line = ""
            repaired_lines.append("") 
            continue
            
        if stripped.startswith(('*', '-', '•', '+')) or re.match(r'^\d+\.', stripped):
            if current_line:
                repaired_lines.append(current_line)
            repaired_lines.append(stripped)
            current_line = ""
        else:
            # [MODIFIED] Allow merging lines after a colon (:) to support inline labels.
            # We only stop merging if the line ends with a sentence-terminator (. ! ?), 
            # OR if it's a special activity log header.
            is_activity_header = "ACTIVITY LOG" in current_line or current_line.strip().endswith("WEEK")
            
            if current_line and not re.search(r'[.!?]$', current_line) and not is_activity_header:
                current_line += " " + stripped
            else:
                if current_line:
                    repaired_lines.append(current_line)
                    # Force a paragraph break after headers or activity logs
                    if is_activity_header:
                        repaired_lines.append("")
                current_line = stripped
                
    if current_line:
        repaired_lines.append(current_line)
        
    return '\n'.join(repaired_lines).strip()

def reconstruct_lists(text: str) -> (str, list):
    """
    Extracts lists separately from normal paragraphs.
    Returns (cleaned text without lists, [list of bullet items])
    """
    lines = text.split('\n')
    normal_text = []
    list_items = []
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            normal_text.append("")
            continue
            
        # Detect numbered/bullet fragments
        if re.match(r'^(\d+\.|\-|\*|•)\s+', stripped):
            content = re.sub(r'^(\d+\.|\-|\*|•)\s+', '', stripped).strip()
            list_items.append(content)
        else:
            normal_text.append(line)
            
    return '\n'.join(normal_text), list_items

def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model

def extract_relevant_sentence(query: str, content: str) -> str:
    """
    Splits content into sentences and returns the single most relevant one.
    """
    if not query or not content:
        return ""
        
    clean_text = clean_markdown_noise(content)
    raw_parts = re.split(r'(?<=[.!?])\s+|\n', clean_text)
    filtered_sentences = []
    
    for p in raw_parts:
        s = p.strip()
        if not s: continue
        
        if len(s) > 15 and not s.endswith(':'):
            s_clean = re.sub(r'^[^\w\s]+', '', s).strip()
            if len(s_clean) > 10:
                filtered_sentences.append(s_clean)

    if not filtered_sentences:
        fallback = re.sub(r'[\s\n]+', ' ', clean_text).strip()
        return (fallback[:150] + "...") if len(fallback) > 150 else fallback
    
    from processing import embedder
    model = embedder.get_model()
    
    query_embedding = model.encode(query, convert_to_tensor=True)
    sentence_embeddings = model.encode(filtered_sentences, convert_to_tensor=True)
    
    scores = util.cos_sim(query_embedding, sentence_embeddings)[0]
    best_idx = scores.argmax().item()
    
    result = filtered_sentences[best_idx]
    if len(result) > 200:
        match = re.search(r'[^.!?]*[.!?]', result)
        if match:
            result = match.group(0)
            
    return result

def merge_sections(sections: list) -> list:
    """
    Groups retrieved sections by document and section name, merging their content.
    """
    if not sections:
        return []
        
    merged_map = {}
    for sec in sections:
        doc_name = sec.get("document_name", "Unknown")
        doc_id = sec.get("document_id", "Unknown")
        sec_name = sec.get("section_name", "Unknown")
        key = (doc_name, sec_name)
        
        content = sec.get("content_text", "")
        # [MODIFIED] We no longer strip numbering from sections here
        # as the SLM is now responsible for structured output.
        
        if key not in merged_map:
            merged_map[key] = {
                "document_name": doc_name,
                "document_id": doc_id,
                "section_name": sec_name,
                "similarity_score": sec.get("similarity_score", 0.0),
                "content_parts": [content]
            }
        else:
            merged_map[key]["content_parts"].append(content)
            if sec.get("similarity_score", 0.0) > merged_map[key]["similarity_score"]:
                merged_map[key]["similarity_score"] = sec.get("similarity_score")
                
    merged_results = []
    for data in merged_map.values():
        data["content_text"] = "\n\n".join(data["content_parts"])
        del data["content_parts"]
        merged_results.append(data)
        
    merged_results.sort(key=lambda x: x["similarity_score"], reverse=True)
    return merged_results

def format_conversational_response(query: str, sections: list) -> str:
    """
    Formats the response by merging chunk text, removing duplicate sentences,
    preserving headings, and appending source metadata.
    """
    merged = merge_sections(sections)
    if not merged:
        return "I'm sorry, I couldn't find any relevant information in the documents to address your request."

    best = merged[0]
    title = best.get("section_name", "Technical Explanation")
    
    # We want to preserve the heading text, so we'll start the markdown with it
    markdown = f"{title}\n\n"

    seen_sentences = set()
    final_paragraphs = []

    for m in merged:
        content = m.get("content_text", "")
        # Remove noisy markdown but keep sentence structure
        clean_content = clean_markdown_noise(content)
        
        paragraphs = clean_content.split('\n\n')
        
        for p in paragraphs:
            stripped_p = p.strip()
            if not stripped_p: continue
            
            # Split into sentences to deduplicate
            # We use a simple regex split on common punctuation
            sentences = re.split(r'(?<=[.!?])\s+', stripped_p)
            unique_sentences = []
            
            for s in sentences:
                s_clean = s.strip().lower()
                # Create a simple fuzzy key by alphanumeric filtering to catch identical semantic sentences
                fuzzy_key = "".join(filter(str.isalnum, s_clean))[:50]
                
                if fuzzy_key and fuzzy_key not in seen_sentences:
                    unique_sentences.append(s)
                    seen_sentences.add(fuzzy_key)
            
            if unique_sentences:
                final_paragraphs.append(" ".join(unique_sentences))

    # Join the final unique paragraphs with single newlines to maintain continuous flow
    if final_paragraphs:
        markdown += "\n\n".join(final_paragraphs)
        markdown += "\n"

    # Source block (V4 Footer Rule: Plain text, no headings/bullets)
    doc_name = best.get("document_name", "Unknown Document")
    doc_id = best.get("document_id", "Unknown")

    markdown += "\n"
    markdown += "Created by Antigravity AI – Building Safe & Reliable Medical Intelligence.\n\n"
    markdown += f"Source: {doc_name}\n"
    markdown += f"Document ID: {doc_id}\n"

    return markdown

def build_markdown_response(document_name, page_number, section_name, content_text, relevant_sentence, similarity_score, unhighlighted_match=None):
    # DEPRECATED: Redirects to conversational logic
    return format_conversational_response("", [{"document_name": document_name, "page_number": page_number, "section_name": section_name, "content_text": content_text, "similarity_score": similarity_score}])

def format_doc_response(query, document_name, page_number, section_name, content_text, similarity_score):
    return format_conversational_response(query, [{"document_name": document_name, "page_number": page_number, "section_name": section_name, "content_text": content_text, "similarity_score": similarity_score}])

def format_multiple_results(sections: list) -> str:
    return format_conversational_response("", sections)
