from retrieval import mode_router
from processing.storage import supabase
import json

def final_test():
    query = "What is zero trust ai architecture"
    mode = "explain"
    print(f"Testing retrieval for: '{query}'")
    
    results = mode_router.handle_query(supabase, query, mode)
    
    if isinstance(results, dict):
        print("\n=== VERIFICATION SUCCESS ===")
        print(f"Primary Doc ID: {results.get('primary_doc_id')}")
        print(f"Mode: {results.get('mode')}")
        
        context = results.get('retrieved_context', [])
        print(f"Retrieved segments: {len(context)}")
        
        # Show first 2 segments as proof
        for i, item in enumerate(context[:3]):
            print(f"\n[{i}] Type: {item['type']}")
            if item['type'] == 'section':
                print(f"    Title: {item['title']}")
            print(f"    Content Snippet: {item['content'][:100]}...")
            
        print("\n=== METADATA ===")
        print(json.dumps(results.get('metadata'), indent=2))
    else:
        print(f"Failed to get structured results. Got: {results}")

if __name__ == "__main__":
    final_test()
