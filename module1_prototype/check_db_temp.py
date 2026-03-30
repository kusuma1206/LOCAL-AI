from processing.storage import supabase
import json

def check():
    print("Checking most recent document in Supabase...")
    res = supabase.table('documents').select('doc_id, filename, document_summary, document_embedding').order('doc_id', desc=True).limit(1).execute()
    
    if not res.data:
        print("No documents found.")
        return
        
    doc = res.data[0]
    print(f"Doc ID: {doc['doc_id']}")
    print(f"Filename: {doc['filename']}")
    
    summary = doc.get('document_summary')
    if summary:
        print(f"Summary Length: {len(summary)}")
        print(f"Summary Preview: {summary[:100]}...")
    else:
        print("Summary: EMPTY")
        
    embedding = doc.get('document_embedding')
    if embedding:
        # embedding might be a list or a string depending on how it's returned
        try:
            if isinstance(embedding, str):
                emb_list = json.loads(embedding)
            else:
                emb_list = embedding
            print(f"Embedding Dimension: {len(emb_list)}")
        except Exception as e:
            print(f"Embedding check failed: {e}")
    else:
        print("Embedding: EMPTY")

if __name__ == "__main__":
    check()
