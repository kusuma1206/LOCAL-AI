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

    # 1. Strip Mermaid diagrams
    text = re.sub(r'graph\s+(TD|LR|BT|RL).*?(\n\s*end|$)', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'subgraph\s+.*?\n.*?end', '', text, flags=re.DOTALL | re.IGNORECASE)
    
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
        
    # 3. Strip large markdown header markers completely
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    
    # 4. Clean inline artifacts
    text = text.replace('___', '').replace('---', '').replace('***', '').replace('**', '')
    
    # 5. Remove lingering code blocks if empty or just noise (keep logic inside if large, but user says drop formatting artifacts)
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    
    # 6. Repair broken paragraphs
    lines = text.split('\n')
    repaired_lines = []
    current_line = ""
    
    for line in lines:
        stripped = line.strip()
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
            if current_line and not re.search(r'[.!?:]$', current_line):
                current_line += " " + stripped
            else:
                if current_line:
                    repaired_lines.append(current_line)
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
        content = re.sub(r'^(#+\s*)?\d+(\.\d+)*\s+', '', content, flags=re.MULTILINE)
        
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
    Strictly follows the template:
    Title
    Key Insight
    Overview
    Details
    Lists
    Source
    """
    merged = merge_sections(sections)
    if not merged:
        return "I'm sorry, I couldn't find any relevant information in the documents to address your request."

    best = merged[0]
    title = best.get("section_name", "Technical Explanation")
    title = re.sub(r'^\d+[\.\d\s]*', '', title)
    title = re.sub(r'[^\x00-\x7F]+', '', title).strip()

    full_content = "\n\n".join(m.get("content_text", "") for m in merged)
    insight = extract_relevant_sentence(query, full_content)

    seen_sentences = set()
    all_paragraphs = []
    all_bullets = set()

    def deduplicate(text):
        nonlocal all_bullets
        clean_text = clean_markdown_noise(text)
        normal_text, extracted_bullets = reconstruct_lists(clean_text)
        
        for bullet in extracted_bullets:
            all_bullets.add(bullet.strip())
            
        paragraphs = normal_text.split('\n\n')
        final_paragraphs = []
        
        for p in paragraphs:
            stripped_p = p.strip()
            if not stripped_p: continue
            
            sentences = re.split(r'(?<=[.!?])\s+', stripped_p)
            unique_sentences = []
            for s in sentences:
                s_clean = s.strip().lower()
                fuzzy_key = "".join(filter(str.isalnum, s_clean))[:40]
                if fuzzy_key and fuzzy_key not in seen_sentences:
                    unique_sentences.append(s)
                    seen_sentences.add(fuzzy_key)
            
            if unique_sentences:
                final_paragraphs.append(" ".join(unique_sentences))
        
        return final_paragraphs

    for m in merged:
        all_paragraphs.extend(deduplicate(m.get("content_text", "")))
        
    # Filter empty paragraphs
    all_paragraphs = [p for p in all_paragraphs if p.strip()]

    # Layout formulation
    markdown = f"{title}\n\n"
    markdown += f"Key Insight\n{insight}\n\n"
    
    if all_paragraphs:
        markdown += f"Overview\n{all_paragraphs[0]}\n\n"
        
    if len(all_paragraphs) > 1:
        details = "\n\n".join(all_paragraphs[1:])
        markdown += f"Details\n{details}\n\n"
        
    if all_bullets:
        bullet_text = "\n".join(f"• {b}" for b in sorted(list(all_bullets)))
        markdown += f"Lists\n{bullet_text}\n\n"

    # Source block
    doc_name = best.get("document_name", "Unknown")
    doc_id = best.get("document_id", "Unknown")

    markdown += "Source\n\n"
    markdown += f"Document: {doc_name}\n"
    markdown += f"Document ID: {doc_id}\n"

    return markdown

def build_markdown_response(document_name, page_number, section_name, content_text, relevant_sentence, similarity_score, unhighlighted_match=None):
    # DEPRECATED: Redirects to conversational logic
    return format_conversational_response("", [{"document_name": document_name, "page_number": page_number, "section_name": section_name, "content_text": content_text, "similarity_score": similarity_score}])

def format_doc_response(query, document_name, page_number, section_name, content_text, similarity_score):
    return format_conversational_response(query, [{"document_name": document_name, "page_number": page_number, "section_name": section_name, "content_text": content_text, "similarity_score": similarity_score}])

def format_multiple_results(sections: list) -> str:
    return format_conversational_response("", sections)
