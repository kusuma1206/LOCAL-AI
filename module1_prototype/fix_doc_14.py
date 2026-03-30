from supabase import create_client, Client
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def fix_doc_14():
    try:
        doc_id = 14
        filepath = "input_docs/Zero_Trust_AI_Architecture.md"
        
        print(f"Fixing metadata for Doc ID {doc_id}...")
        
        # 1. Re-generate summary and embedding
        from processing import extractor, section_summarizer, embedder
        lines = extractor.extract_document_text(filepath)
        full_text = "\n".join(lines)
        global_doc_summary = section_summarizer.generate_section_summary(full_text[:8000])
        
        model = embedder.get_model()
        document_embedding = model.encode([global_doc_summary])[0].tolist()
        
        # 2. Update the record
        data = {
            "document_summary": global_doc_summary,
            "document_embedding": document_embedding
        }
        
        res = supabase.table("documents").update(data).eq("doc_id", doc_id).execute()
        
        if res.data:
            print(f"Successfully updated Doc ID {doc_id} with metadata.")
        else:
            print(f"Failed to update Doc ID {doc_id}. Row not found or error occurred.")
            
    except Exception as e:
        print(f"Error fixing doc: {e}")

if __name__ == "__main__":
    fix_doc_14()
