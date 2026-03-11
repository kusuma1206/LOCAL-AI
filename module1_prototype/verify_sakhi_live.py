from retrieval import mode_router
from processing.storage import supabase
import json
import sys

# Ensure UTF-8 for Windows terminal emojis
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

def test_live_sakhi():
    query = "How does the Sakhi chat interaction POST /sakhi/chat work?"
    output = []
    output.append(f"--- Running Live Query: '{query}' ---")
    
    # We use 'id_only' first to see what sections we get
    results = mode_router.handle_query(supabase, query, mode="id_only")
    
    output.append("\n[Retrieved Sections]")
    for sec in results.get("top_sections", []):
        output.append(f"- {sec['section_title']} (Score: {sec['similarity_score']:.4f})")
    
    # Now we can test the formatter on the top result
    if results.get("top_sections"):
        from retrieval.response_formatter import format_doc_response
        best_sec = results["top_sections"][0]
        
        # We need the full content for the formatter. 
        # Fetch the summary from the sections table
        section_id = best_sec['section_id']
        sec_res = supabase.table("sections").select("section_summary").eq("id", section_id).execute()
        
        content = sec_res.data[0].get("section_summary", "No summary in DB.") if sec_res.data else "No summary in DB."

        formatted = format_doc_response(
            query=query,
            document_name="Sakhi Backend", # Placeholder if not in results
            page_number=1,
            section_name=best_sec['section_title'],
            content_text=content,
            similarity_score=best_sec['similarity_score']
        )
        output.append("\n[Formatted Response Output]")
        output.append("="*40)
        output.append(formatted)
        output.append("="*40)

    # Save to file explicitly in UTF-8
    with open("sakhi_live_result_final.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(output))
    print("Live result written to sakhi_live_result_final.txt")

if __name__ == "__main__":
    test_live_sakhi()
