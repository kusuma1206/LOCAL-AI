import numpy as np
import os
import hashlib
from supabase import create_client, Client

INDEX_FILE = "vector_store/index.faiss"

# Supabase Config
SUPABASE_URL = "https://vcaxpwrkhfbymgcyhvmk.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZjYXhwd3JraGZieW1nY3lodm1rIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzIwNzc1NTgsImV4cCI6MjA4NzY1MzU1OH0.f4LQHfzIoyNOoBTkLDuEljeLNcTY56XTX_6PE4Svygg"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# Storage Intelligence configuration
EXPECTED_DIMENSION = 384

def save_to_vector_store(processed_chunks, file_path=None):
    """
    Vector Storage Intelligence Engine: validates, deduplicates, and stores chunks.
    Ensures semantic memory integrity via hash-based idempotency.
    """
    if not processed_chunks:
        print("  [Storage Warning] No processed chunks provided for storage.")
        return False

    try:
        # 1. Dimension Integrity Check
        embeddings = np.array([c["embedding"] for c in processed_chunks]).astype('float32')
        current_dim = embeddings.shape[1]
        
        if current_dim != EXPECTED_DIMENSION:
            print(f"  [Storage Failure] Dimension mismatch detected. Got {current_dim}, expected {EXPECTED_DIMENSION}.")
            return False

        # 2. Local FAISS Storage (Snapshot of current batch)
        import faiss
        index = faiss.IndexFlatL2(EXPECTED_DIMENSION)
        index.add(embeddings)
        os.makedirs(os.path.dirname(INDEX_FILE), exist_ok=True)
        faiss.write_index(index, INDEX_FILE)
        print(f"  [FAISS Index] Successfully updated with {index.ntotal} local vectors.")

        # 3. Supabase Storage (Atomic Idempotent Logic)
        print("  [Supabase Storage] Synchronising with cloud vector store...")
        filename = os.path.basename(file_path) if file_path else "unknown"

        stats = {"inserted": 0, "updated": 0, "skipped": 0, "failed": 0}

        for i, chunk_data in enumerate(processed_chunks):
            content = chunk_data.get("chunk_text", "")
            embedding = chunk_data.get("embedding")
            metadata = chunk_data.get("metadata", {})
            
            # Extract persistence signals
            model_name = metadata.get("embedding_model", "unknown")
            dim = metadata.get("embedding_dimension", EXPECTED_DIMENSION)
            
            # Generate deterministic hash for the chunk content
            chunk_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()

            try:
                # 4. Idempotency Check: lookup by hash
                existing = supabase.table("document_chunks").select("id", "content").eq("chunk_hash", chunk_hash).execute()
                
                if existing.data:
                    stored_content = existing.data[0].get("content")
                    record_id = existing.data[0].get("id")
                    
                    if stored_content == content:
                        # Identical match: Skip to preserve integrity & credits
                        # print(f"    - [{i}] Duplicate vector skipped")
                        stats["skipped"] += 1
                        continue
                    else:
                        # 5. Atomic Update: Content has changed, refresh vector
                        payload = {
                            "content": content,
                            "embedding": embedding
                        }
                        supabase.table("document_chunks").update(payload).eq("id", record_id).execute()
                        print(f"    - [{i}] Existing vector updated (content change)")
                        stats["updated"] += 1
                else:
                    # 6. New Vector Insertion
                    payload = {
                        "content": content,
                        "embedding": embedding,
                        "chunk_hash": chunk_hash
                    }
                    supabase.table("document_chunks").insert(payload).execute()
                    # print(f"    - [{i}] New vector inserted")
                    stats["inserted"] += 1
                    
            except Exception as e:
                print(f"    [!] Storage failure detected for chunk {i}: {e}")
                stats["failed"] += 1

        print(f"  [Storage Summary] New: {stats['inserted']} | Updated: {stats['updated']} | Skipped: {stats['skipped']} | Failed: {stats['failed']}")
        return True

    except Exception as e:
        print(f"  [Vector Engine Failure] Critical error during storage operation: {e}")
        return False

def insert_section(supabase, document_id, section_title, section_summary, section_embedding):
    """
    Inserts a section into the sections table for Hierarchical RAG.
    """
    try:
        data = {
            "document_id": document_id,
            "section_title": section_title,
            "section_summary": section_summary,
            "section_embedding": section_embedding
        }
        response = supabase.table("sections").insert(data).execute()
        
        if not response.data:
            raise Exception("Failed to insert section: No data returned")
            
        section_id = response.data[0]["id"]
        print(f"  [Hierarchical Storage] Section inserted: {section_title} (ID: {section_id})")
        return section_id
        
    except Exception as e:
        print(f"  [Hierarchical Storage Failure] Could not insert section: {e}")
        raise

def insert_chunk_with_section(supabase, section_id, content, embedding, chunk_hash):
    """
    Inserts a chunk into document_chunks with a foreign key to its section.
    """
    try:
        data = {
            "section_id": section_id,
            "content": content,
            "embedding": embedding,
            "chunk_hash": chunk_hash
        }
        supabase.table("document_chunks").insert(data).execute()
        print(f"  [Hierarchical Storage] Chunk inserted under section_id: {section_id}")
        return True
        
    except Exception as e:
        print(f"  [Hierarchical Storage Failure] Could not insert chunk under section: {e}")
        return False

def upsert_document(supabase, document_id, file_path, document_summary=None):
    """
    Ensures a document record exists and optionally updates its summary.
    """
    try:
        data = {
            "id": document_id,
            "filename": os.path.basename(file_path),
            "document_summary": document_summary
        }
        # Using upsert to handle existing document_id
        supabase.table("documents").upsert(data).execute()
        print(f"  [Storage] Document upserted: {document_id}")
        return True
    except Exception as e:
        print(f"  [Storage Failure] Could not upsert document: {e}")
        return False

def delete_document_records(supabase, document_id):
    """
    Clears all existing sections and chunks for a given document_id.
    Ensures a fresh state for hierarchical ingestion.
    """
    try:
        # 1. Get all section IDs for this document
        sections_res = supabase.table("sections").select("id").eq("document_id", document_id).execute()
        section_ids = [s["id"] for s in sections_res.data]
        
        if section_ids:
            # 2. Delete chunks associated with these sections
            supabase.table("document_chunks").delete().in_("section_id", section_ids).execute()
            
            # 3. Delete the sections themselves
            supabase.table("sections").delete().eq("document_id", document_id).execute()
            
        print(f"  [Storage Clean-up] Old records cleared for document_id: {document_id}")
        return True
    except Exception as e:
        print(f"  [Storage Clean-up Failure] Could not clear old records: {e}")
        return False
def insert_query_log(supabase, query, mode, section_ids, chunk_ids, scores, gen_time_ms, response):
    """
    Inserts a query audit record into the query_logs table.
    """
    try:
        data = {
            "query": query,
            "mode": mode,
            "retrieved_section_ids": section_ids,
            "retrieved_chunk_ids": chunk_ids,
            "similarity_scores": scores,
            "generation_time_ms": gen_time_ms,
            "response_text": response
        }
        # Ensure we use the correct table name public.query_logs usually works if schema is public
        # If the user saw 'Could not find the table', it might be a caching issue or missing table.
        supabase.table("query_logs").insert(data).execute()
        print("Query audit record stored")
        return True
    except Exception as e:
        print(f"  [Audit Failure] Could not store query log: {e}")
        return False
