import traceback
from retrieval.document_retriever import retrieve_document_sections
from processing.storage import supabase

try:
    print("Testing specific section API query...")
    res = supabase.table("sections").select("id, title").eq("document_id", 5).execute()
    print("Direct query success:", len(res.data))
    
    txt = retrieve_document_sections(supabase, 5)
    print("Function success. Length:", len(txt))
except Exception as e:
    print("Exception caught:")
    print(e)
