import os
import re
import argparse
from pathlib import Path
from typing import Optional
from processing import validator, extractor, cleaner, structure_analyzer, chunker, embedder, storage, section_summarizer
from config import settings

def log_debug(message):
    log_path = "pipeline_debug.log"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"{message}\n")
    print(message)

def run_ingestion_pipeline(file_path, title=None, sharepoint_url=None, sharepoint_file_id=None, uploaded_by=None, doc_id_override=None, onedrive_item_id=None):
    try:
        log_debug(f"--- Pipeline Start: {file_path} (ID: {doc_id_override}) ---")

        # Step 1: Download from OneDrive if item_id provided
        if onedrive_item_id:
            log_debug(f"  [Pipeline] Downloading from OneDrive: {onedrive_item_id}")
            from processing.sharepoint import download_from_onedrive
            try:
                downloaded_bytes = download_from_onedrive(onedrive_item_id)
                with open(file_path, "wb") as f:
                    f.write(downloaded_bytes)
                log_debug("  - Content downloaded successfully.")
            except Exception as e:
                log_debug(f"  [!] OneDrive Download Step Failed: {e}. Falling back to local copy.")

        # 1. Validation
        val_result = validator.validate_document(file_path)
        status = val_result["status"]
        message = val_result["message"]
        document_id = val_result.get("document_id", "unknown")

        if status == "INVALID":
            log_debug(f"Validation Failed: {message}")
            return
        
        if status == "DUPLICATE_DETECTED" and not doc_id_override:
            log_debug(f"Duplicate Detection: {message}")
            return

        log_debug(f"Validation Status: {status}")
        
        # 3. Extraction
        try:
            ext_result = extractor.extract_text(file_path)
            raw_text = ext_result["text"]
            log_debug(f"Text Extracted. Length: {len(raw_text)}")

            if not raw_text:
                log_debug("Extraction Failed: No text content.")
                if doc_id_override:
                    storage.update_document_status(doc_id_override, "error")
                return
        except Exception as e:
            log_debug(f"Extraction Failed: {e}")
            if doc_id_override:
                storage.update_document_status(doc_id_override, "error")
            return

        # 4. Cleaning
        clean_result = cleaner.clean_text(raw_text)
        cleaned_text = clean_result["cleaned_text"]
        log_debug(f"Noise Reduction: {clean_result['noise_reduction_percent']}%")

        # 4.5 Update status (Do NOT delete record here, as it was just created in api.py)
        if doc_id_override:
            log_debug(f"  [Pipeline] Updating status to processing for ID: {doc_id_override}")
            storage.update_document_status(doc_id_override, "processing")
            if sharepoint_url:
                log_debug(f"  [Pipeline] Received sharepoint_url: {sharepoint_url}")

        # Step 3 & 4. Hierarchical Structure Analysis
        if doc_id_override:
            log_debug(f"  [Pipeline] Updating status to chunking.")
            storage.update_document_status(doc_id_override, "chunking")
        
        cleaned_lines = [line.strip() for line in cleaned_text.split('\n') if line.strip()]
        log_debug(f"  [Pipeline] Building section tree.")
        sections = structure_analyzer.build_section_tree(cleaned_lines, doc_id_override or document_id)
        log_debug(f"  [Pipeline] Detected {len(sections)} sections.")
        
        # 4.7 Global Document Summary
        log_debug(f"  [Pipeline] Generating 'Drip-Fed' summary.")
        global_doc_summary = section_summarizer.generate_section_summary(cleaned_text)
        log_debug(f"  [Pipeline] Summary generated.")
        
        # Step 5. Embedding
        if doc_id_override:
            log_debug(f"  [Pipeline] Updating status to embedding.")
            storage.update_document_status(doc_id_override, "embedding")

        model = embedder.get_model()
        log_debug("Generating Document-level Embedding...")
        document_embedding = model.encode([global_doc_summary])[0].tolist()
        
        log_debug(f"Updating document metadata in Supabase...")
        doc_id = storage.upsert_document(
            storage.supabase, 
            doc_id_override or document_id, 
            file_path, 
            global_doc_summary, 
            document_embedding,
            title=title,
            sharepoint_url=sharepoint_url,
            sharepoint_file_id=onedrive_item_id or sharepoint_file_id,
            uploaded_by=uploaded_by
        )
        
        if doc_id is None:
            log_debug(" [!] Critical Error: Document ID could not be updated.")
            return

        log_debug(f"Starting hierarchical section/chunk processing for doc_id: {doc_id}")
        for section in sections:
            section_title = section["title"]
            section_content = section["content"]
                
            try:
                # 5. Section Summarization & Embedding
                # Fix: Handle empty content for hierarchical integrity
                summary = section_summarizer.generate_section_summary(section_content or "")
                embedding_input = f"{section_title} {section_content[:500]}" if section_content else section_title
                summary_embedding = model.encode([embedding_input])[0].tolist()
                
                # 6. Section Storage (Always insert, even if empty)
                s_id = storage.insert_section(
                    storage.supabase, doc_id, section_title, summary, summary_embedding,
                    section_id=section.get("section_id"),
                    parent_id=section.get("parent_section_id"),
                    level=section.get("level", 1),
                    order=section.get("section_order", 1)
                )
                
                # 7. Chunking (Only if content exists)
                if not section_content:
                    continue

                chunks = chunker.chunk_text([section], settings.CHUNK_SIZE, settings.CHUNK_OVERLAP)
                if not chunks: 
                    continue
                    
                embeddings = model.encode([c["chunk_text"] for c in chunks]).tolist()
                
                for i, chunk_data in enumerate(chunks):
                    storage.insert_document_chunk(
                        storage.supabase, s_id, chunk_data["chunk_text"], embeddings[i], chunk_index=i + 1
                    )
            except Exception as e:
                log_debug(f"  [!] Atomic Failure for section {section_title}: {e}")

        # Final Status Update
        storage.update_document_status(doc_id, "ready")
        log_debug(f"--- Pipeline Finished Successfully for ID: {doc_id} ---")

    except Exception as e:
        import traceback
        error_msg = f"  [CRITICAL PIPELINE ERROR] {str(e)}\n{traceback.format_exc()}"
        log_debug(error_msg)
        if doc_id_override:
            storage.update_document_status(doc_id_override, "error")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hierarchical RAG Production Pipeline")
    parser.add_argument("document_path", help="Path to document for ingestion")
    args = parser.parse_args()
    run_ingestion_pipeline(args.document_path)
