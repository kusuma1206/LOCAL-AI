import numpy as np
import os
import hashlib
from supabase import create_client, Client
from config import settings

# Supabase Config from centralized settings
SUPABASE_URL = settings.SUPABASE_URL
SUPABASE_KEY = settings.SUPABASE_KEY

if not SUPABASE_URL or not SUPABASE_KEY:
    print("  [Critical Warning] SUPABASE_URL or SUPABASE_KEY not found in environment!")

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

def insert_section(supabase, doc_id, title, summary, section_embedding, 
                   section_id=None, parent_id=None, level=1, order=1):
    """
    Inserts a section into the sections table for Hierarchical RAG using NEW schema.
    """
    import uuid
    try:
        data = {
            "section_id": str(section_id) if section_id else str(uuid.uuid4()),
            "document_id": doc_id,
            "title": title,
            "section_summary": summary,
            "section_embedding": section_embedding,
            "level": level,
            "section_order": order
        }
        if parent_id:
            data["parent_section_id"] = parent_id
            
        response = supabase.table("sections").insert(data).execute()
        
        if not response.data:
            raise Exception("Failed to insert section: No data returned")
            
        s_id = response.data[0]["section_id"]
        # print(f"  [Hierarchical Storage] Section inserted: {title} (ID: {s_id})")
        return s_id
        
    except Exception as e:
        print(f"  [Hierarchical Storage Failure] Could not insert section {title}: {e}")
        raise

def insert_document_chunk(supabase, section_id, content, embedding, chunk_index=None):
    """
    Inserts a chunk into document_chunks with a foreign key to its section.
    Aligned with NEW schema. Generates a fresh UUID for chunk_id.
    """
    import uuid
    try:
        data = {
            "chunk_id": str(uuid.uuid4()),
            "section_id": section_id,
            "content": content,
            "embedding": embedding,
            "chunk_index": chunk_index
        }
        supabase.table("document_chunks").insert(data).execute()
        return True
    except Exception as e:
        print(f"  [Hierarchical Storage Failure] Could not insert chunk under section: {e}")
        return False

def upsert_document(supabase, document_id, file_path, document_summary=None, document_embedding=None, 
                    title=None, sharepoint_url=None, sharepoint_file_id=None, uploaded_by=None):
    """
    Ensures a document record exists. 
    Note: if document_id is UUID, we might need a doc_id (int).
    For now, we use upsert on doc_id if it's an int, or fallback to file-based lookup.
    """
    try:
        # If document_id is an int, use it as doc_id
        doc_id = None
        if isinstance(document_id, int):
            doc_id = document_id
        
        data = {
            "filename": os.path.basename(file_path),
            "title": title or os.path.basename(file_path),
            "document_summary": document_summary,
            "document_embedding": document_embedding,
            "storage_url": sharepoint_url,
            "user_id": uploaded_by
        }
        
        if doc_id:
            data["doc_id"] = doc_id
            
        res = supabase.table("documents").upsert(data, on_conflict="doc_id" if doc_id else "filename").execute()
        
        if hasattr(res, 'error') and res.error:
            raise Exception(f"Supabase Error: {res.error}")

        if res.data:
            return res.data[0].get("doc_id")
        return None
    except Exception as e:
        print(f"  [Storage Failure] Could not upsert document {file_path}: {e}")
        return None

def create_document(title: str, filename: str, file_hash: str = None) -> int:
    """
    Inserts a new document record and returns the generated integer doc_id.
    Includes the file_hash for content-based duplicate detection.
    """
    try:
        data = {
            "title": title,
            "filename": filename,
            "status": "uploading",
            "file_hash": file_hash
        }
        response = supabase.table("documents").insert(data).execute()
        
        if response.data:
            doc_id = response.data[0].get("doc_id")
            print(f"  [Storage] Document created. doc_id: {doc_id}")
            return doc_id
        return None
    except Exception as e:
        print(f"  [Storage Failure] Could not create document: {e}")
        return None

def log_ingestion_event(event: str, file_name: str, old_doc_id: int = None, new_doc_id: int = None, metadata: dict = None):
    """
    Logs an ingestion event (e.g., document replacement) to the ingestion_logs table.
    """
    try:
        data = {
            "event": event,
            "file_name": file_name,
            "old_document_id": old_doc_id,
            "new_document_id": new_doc_id,
            "metadata": metadata
        }
        supabase.table("ingestion_logs").insert(data).execute()
        print(f"  [Audit] Ingestion event logged: {event} for {file_name}")
        return True
    except Exception as e:
        print(f"  [Audit Failure] Could not log ingestion event: {e}")
        return False

def update_document_status(doc_id: int, status: str, storage_url: str = None):
    """
    Updates the status and optionally the storage_url for a document.
    """
    try:
        data = {"status": status}
        if storage_url:
            data["storage_url"] = storage_url
            
        supabase.table("documents").update(data).eq("doc_id", doc_id).execute()
        print(f"  [Storage] Document {doc_id} status updated to: {status}")
        return True
    except Exception as e:
        print(f"  [Storage Failure] Could not update document status: {e}")
        return False

def delete_document_complete(doc_id: int):
    """
    Safely deletes a document and all its associated records (chunks, sections).
    Follows the dependency hierarchy to ensure a clean slate.
    """
    try:
        # 1. Fetch all section IDs for this document
        sections_res = supabase.table("sections").select("section_id").eq("document_id", doc_id).execute()
        section_ids = [s["section_id"] for s in sections_res.data]
        
        if section_ids:
            # 2. Delete chunks associated with these sections
            supabase.table("document_chunks").delete().in_("section_id", section_ids).execute()
            print(f"  [Clean-up] Chunks deleted for sections of doc_id: {doc_id}")
            
            # 3. Delete the sections themselves
            supabase.table("sections").delete().eq("document_id", doc_id).execute()
            print(f"  [Clean-up] Sections deleted for doc_id: {doc_id}")
        
        # 4. Delete the document metadata itself
        supabase.table("documents").delete().eq("doc_id", doc_id).execute()
        print(f"  [Clean-up] Document record deleted for doc_id: {doc_id}")
        
        return True
    except Exception as e:
        print(f"  [Clean-up Failure] Critical error during document deletion: {e}")
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
        supabase.table("query_logs").insert(data).execute()
        return True
    except Exception as e:
        print(f"  [Audit Failure] Could not store query log: {e}")
        return False

def search_chunks(supabase, query_embedding: list, top_k: int = 5) -> list:
    """
    Retrieves the top matching chunks using pure Python cosine similarity fallback.
    Aligned with NEW schema (chunk_id, section_id, content, embedding).
    """
    import numpy as np
    
    try:
        # Fetch all chunks
        response = supabase.table("document_chunks").select("chunk_id, section_id, content, embedding").execute()
        
        if not response.data:
            return []
            
        chunks = response.data
        q_vec = np.array(query_embedding).astype('float32')
        q_norm = np.linalg.norm(q_vec)
        
        if q_norm == 0:
            return []
            
        import ast
        results = []
        for i, c in enumerate(chunks):
            raw_emb = c.get("embedding")
            
            if not raw_emb:
                continue
                
            if isinstance(raw_emb, str):
                try:
                    raw_emb = ast.literal_eval(raw_emb)
                except:
                    continue
                    
            c_vec = np.array(raw_emb).astype('float32')
            if len(c_vec) == 0:
                continue
                
            c_norm = np.linalg.norm(c_vec)
            if c_norm == 0:
                continue
                
            # Compute Cosine Similarity
            sim = np.dot(q_vec, c_vec) / (q_norm * c_norm)
            
            results.append({
                "chunk_id": c.get("chunk_id"),
                "section_id": c.get("section_id"),
                "content": c.get("content"),
                "similarity_score": float(sim)
            })
            
        # Sort by highest similarity
        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        return results[:top_k]
        
    except Exception as e:
        import traceback
        print(f"  [Storage Failure] Vector search failed: {e}\n{traceback.format_exc()}")
        return []

def expand_section(section_id: str) -> str:
    """
    Retrieves all chunks matching a section_id, orders them by chunk_index,
    and merges their content into a full section text block.
    """
    try:
        response = supabase.table("document_chunks") \
            .select("content") \
            .eq("section_id", section_id) \
            .order("chunk_index") \
            .execute()
            
        if not response.data:
            return ""
            
        merged_content = "\n\n".join([chunk.get("content", "").strip() for chunk in response.data])
        return merged_content
    except Exception as e:
        print(f"  [Storage Failure] Could not expand section {section_id}: {e}")
        return ""
