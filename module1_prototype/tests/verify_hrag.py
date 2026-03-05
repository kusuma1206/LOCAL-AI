# Mocking modules before they are imported by anything in basic RAG
import sys
from unittest.mock import MagicMock, patch

sys.modules['torch'] = MagicMock()
sys.modules['transformers'] = MagicMock()
sys.modules['sentence_transformers'] = MagicMock()

# Mocking internal components that load heavy models
from retrieval import mode_router

def test_hrag_context_enrichment():
    print("Running 3-Level HRAG Context Enrichment Test (UUID-Native)...")
    
    # Valid deterministic UUIDs for testing
    DOC_UUID = "6ba7b810-9dad-11d1-80b4-00c04fd430c8" # DNS Namespace as proxy
    SEC_UUID_1 = "550e8400-e29b-41d4-a716-446655440000"
    SEC_UUID_2 = "550e8400-e29b-41d4-a716-446655440001"
    
    mock_supabase = MagicMock()
    
    # Mocking Level 3: Chunks
    mock_chunks = [
        {"chunk_text": "Detailed content about Pilot Prototype revenue model.", "section_id": SEC_UUID_1},
        {"chunk_text": "Access control details for secure data sharing.", "section_id": SEC_UUID_2}
    ]
    
    # Mocking Level 2: Sections
    mock_sections = [
        {"section_id": SEC_UUID_1, "document_id": DOC_UUID, "section_title": "Revenue Model", "similarity_score": 0.9},
        {"section_id": SEC_UUID_2, "document_id": DOC_UUID, "section_title": "Security", "similarity_score": 0.8}
    ]
    
    # Mocking Level 2 Summaries
    mock_summaries = [
        {"section_title": "Revenue Model", "section_summary": "Sustainable growth through commission-based earnings."},
        {"section_title": "Security", "section_summary": "Robust access control for data integrity."}
    ]

    # Mocking Level 1 Global Document Summary
    mock_doc = [{"document_summary": "The Pilot Prototype is a comprehensive full-stack system for secure project collaboration."}]
    
    with patch('retrieval.query_embedder.embed_query', return_value=[0.1]*512), \
         patch('retrieval.section_retriever.retrieve_top_sections', return_value=mock_sections), \
         patch('retrieval.chunk_retriever.retrieve_top_chunks', return_value=mock_chunks), \
         patch('retrieval.slm_generator.SLMGenerator.generate_explanation', return_value="Mocked Response") as mock_gen, \
         patch('processing.storage.insert_query_log'):
        
        # Mocking the Supabase chain for Level 2 and Level 1
        # Level 1 fetch (documents)
        mock_supabase.table("documents").select().eq().execute.return_value.data = mock_doc
        # Level 2 fetch (sections)
        mock_supabase.table("sections").select().in_().execute.return_value.data = mock_summaries
        
        query = "Explain Pilot Prototype"
        mode_router.handle_query(mock_supabase, query, mode="explain")
        
        # Verify that generate_explanation was called with 3-level enriched context
        args, kwargs = mock_gen.call_args
        context = args[1]
        
        print(f"Context passed to SLM (Length: {len(context)}):")
        for i, c in enumerate(context):
            print(f"  [{i}] {c[:100]}...")
            
        assert any("GLOBAL DOCUMENT OVERVIEW" in c for c in context)
        assert any("SECTION OVERVIEW for 'Revenue Model'" in c for c in context)
        assert any("DETAILED CONTENT: Detailed content" in c for c in context)
        print("SUCCESS: 3-Level HRAG Context Enrichment with UUIDs verified.")

if __name__ == "__main__":
    try:
        test_hrag_context_enrichment()
    except Exception as e:
        print(f"FAILED: {e}")
        sys.exit(1)
