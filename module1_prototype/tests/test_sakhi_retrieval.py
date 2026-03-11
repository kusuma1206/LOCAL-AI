import sys
import os

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from retrieval import mode_router
from processing.storage import supabase
from retrieval.response_formatter import format_doc_response

# Ensure UTF-8 for Windows terminal emojis
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

def run_sakhi_verification():
    """
    Performs a live retrieval and formatting test using the Sakhi WhatsApp Backend documents.
    """
    query = "How does the Sakhi chat interaction POST /sakhi/chat work?"
    print(f"--- Running Sakhi Verification Query: '{query}' ---")
    
    # 1. Retrieve metadata
    results = mode_router.handle_query(supabase, query, mode="id_only")
    
    if not results.get("top_sections"):
        print("Error: No sections found in database. Ensure Sakhi document is indexed.")
        return

    best_sec = results["top_sections"][0]
    print(f"Match Found: {best_sec['section_title']} (Score: {best_sec['similarity_score']:.4f})")
    
    # 2. Fetch full content summary from DB
    section_id = best_sec['section_id']
    sec_res = supabase.table("sections").select("section_summary").eq("id", section_id).execute()
    
    if not sec_res.data:
        print("Error: Could not find section summary in database.")
        return
        
    content = sec_res.data[0].get("section_summary", "")

    # 3. Format result
    formatted = format_doc_response(
        query=query,
        document_name="Sakhi Backend",
        page_number=1,
        section_name=best_sec['section_title'],
        content_text=content,
        similarity_score=best_sec['similarity_score']
    )
    
    print("\n--- Formatted Intelligent Response ---")
    print(formatted)
    print("--------------------------------------")

if __name__ == "__main__":
    run_sakhi_verification()
