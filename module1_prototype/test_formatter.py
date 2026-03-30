import traceback
from retrieval.response_formatter import format_conversational_response

try:
    # Build pseudo-chunk results that mimic DB exact output
    sections = [
        {
            "section_name": "Layer 1: Similarity Gate",
            "document_name": "Zero_Trust_AI_Architecture.md",
            "document_id": "1",
            "similarity_score": 0.95,
            "content_text": "The Similarity Gate validates user queries against trusted knowledge before allowing the AI model to process them."
        },
        {
            "section_name": "Layer 1: Similarity Gate",
            "document_name": "Zero_Trust_AI_Architecture.md",
            "document_id": "1",
            "similarity_score": 0.92,
            "content_text": "The Similarity Gate validates user queries against trusted knowledge before allowing the AI model to process them. It acts as an early abort mechanism."
        }
    ]
    
    print("\n--- OUTPUT FORMAT ---")
    txt = format_conversational_response("What is the gate?", sections)
    print(txt)
except Exception as e:
    print(traceback.format_exc())
