import os
import shutil
from pathlib import Path

import hashlib
from config import settings
from processing import validator, extractor, cleaner, chunker, embedder, storage, structure_analyzer, metadata_builder, section_summarizer

def run_ingestion_pipeline(file_path):
    print(f"\n{'='*50}")
    print(f"Starting Hierarchical Ingestion Pipeline for: {file_path}")
    print(f"{'='*50}")

    # 1. Validation
    val_result = validator.validate_document(file_path)
    status = val_result["status"]
    message = val_result["message"]
    warnings = val_result["warnings"]
    document_id = val_result.get("document_id", "unknown")

    if status == "INVALID":
        print(f"Validation Failed: {message}")
        return
    
    if status == "DUPLICATE_DETECTED":
        print(f"Duplicate Detection: {message}")
        return

    print(f"Validation Status: {status}")
    if message:
        print(f"Message: {message}")
    
    for warning in warnings:
        print(f"Warning: {warning}")

    # Skip semantic processing for scanned PDFs
    if status == "VALID_WITH_WARNING" and any("OCR recommended" in w for w in warnings):
        print("Semantic processing skipped — OCR required.")
        return

    # 2. Mock OneDrive Upload (Copy to onedrive_mock with ID assignment)
    mock_filename = f"{document_id}_{Path(file_path).name}"
    mock_dest = Path(settings.ONEDRIVE_MOCK_DIR) / mock_filename
    os.makedirs(settings.ONEDRIVE_MOCK_DIR, exist_ok=True)
    shutil.copy2(file_path, mock_dest)
    print(f"File copied to OneDrive Mock: {mock_dest}")
    print(f"Assigned Document ID: {document_id}")

    # 3. Extraction
    try:
        ext_result = extractor.extract_text(file_path)
        raw_text = ext_result["text"]
        confidence = ext_result["confidence"]
        ext_warnings = ext_result["warnings"]

        print(f"Text Extracted. Length: {len(raw_text)} characters.")
        print(f"Extraction Confidence: {confidence:.2f}")
        for warning in ext_warnings:
            print(f"Extraction Warning: {warning}")

        if not raw_text:
            print("Extraction Failed: No text content.")
            return
    except Exception as e:
        print(f"Extraction Failed: {e}")
        return

    # 4. Cleaning
    clean_result = cleaner.clean_text(raw_text)
    cleaned_text = clean_result["cleaned_text"]
    lines_rem = clean_result["lines_removed"]
    reduction = clean_result["noise_reduction_percent"]

    print("\nNoise Suppression:")
    print(f"Lines Removed: {lines_rem}")
    print(f"Noise Reduction: {reduction}%")
    print(f"Cleaned Text Length: {len(cleaned_text)} characters.")

    # 4.5 Structure Analysis
    sections = structure_analyzer.analyze_structure(cleaned_text)
    report = structure_analyzer.get_structure_report(sections, len(cleaned_text))
    
    print("\nDetected Sections:")
    for entry in report['distribution']:
        print(f"Section Title: {entry['title']}")
        print(f"Content Length: {entry['len']}")
    
    print("\nSegmentation Summary:")
    print(f"Total Sections: {report['summary']['total_sections']}")
    
    if report['warnings']:
        print("\nStructure Warnings:")
        for warning in report['warnings']:
            print(f"  [!] {warning}")

    # 4.6 Section Validation Visibility
    print(f"\n=== DETECTED SECTIONS ===")
    for section in sections:
        print(f"TITLE: {section['section_title']}")

    # --- HIERARCHICAL INGESTION ENGINE ---
    print(f"\nStarting fresh hierarchical ingestion")
    
    # 4.7 Global Document Summary (Level 1 of HRAG)
    print("Generating Comprehensive Global Document Summary...")
    # Increase context to 8000 chars to capture more of the document for the global summary
    global_doc_summary = section_summarizer.generate_section_summary(cleaned_text[:8000])
    
    # Clean up old records for this document and ensure document entry exists
    storage.delete_document_records(storage.supabase, document_id)
    storage.upsert_document(storage.supabase, document_id, file_path, global_doc_summary)
    
    print(f"Engaging Hierarchical Ingestion Flow...")
    
    model = embedder.get_model()
    
    for section in sections:
        section_title = section["section_title"]
        section_content = section["content"]
        
        if not section_content:
            continue
            
        print(f"\n  Processing section: <{section_title}>")
        
        try:
            # 5. Section Summarization & Embedding
            summary = section_summarizer.generate_section_summary(section_content)
            
            # 5.5 Section Embedding (Title + Preview)
            embedding_input = f"{section_title} {section_content[:500]}"
            print(f"  Section embedding generated from title + preview content")
            summary_embedding = model.encode([embedding_input])[0].tolist()
            
            # 6. Section Storage
            section_id = storage.insert_section(
                storage.supabase, 
                document_id, 
                section_title, 
                summary, 
                summary_embedding
            )
            print(f"  Section stored with ID: {section_id}")
            
            # 7. Chunking (Structure-Aware)
            # chunk_text expects a list of sections, we provide a single one
            chunks = chunker.chunk_text([section], settings.CHUNK_SIZE, settings.CHUNK_OVERLAP)
            
            # 8. Metadata Enrichment & Chunk Embedding
            pipeline_context = {
                "file_path": file_path,
                "file_type": Path(file_path).suffix[1:].upper(),
                "extraction_confidence": confidence,
                "noise_reduction_percent": reduction,
                "document_id": document_id,
                "section_id": section_id
            }
            enriched_chunks = metadata_builder.build_metadata(chunks, pipeline_context)
            final_processed_chunks = embedder.generate_embeddings(enriched_chunks)
            
            # 9. Chunk Storage (with foreign key)
            for chunk_data in final_processed_chunks:
                content = chunk_data.get("chunk_text", "")
                embedding = chunk_data.get("embedding")
                chunk_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
                
                storage.insert_chunk_with_section(
                    storage.supabase,
                    section_id,
                    content,
                    embedding,
                    chunk_hash
                )
            
            print(f"  Chunks stored under section: {section_id}")
            
        except Exception as e:
            print(f"  [!] Atomic Failure: Skipping section <{section_title}> due to error: {e}")
            continue

    print(f"\n{'='*50}")
    print("Hierarchical Ingestion Pipeline completed successfully.")
    print(f"{'='*50}\n")

import argparse
from retrieval import mode_router

def run_retrieval_flow(query, mode):
    """
    Executes the hierarchical retrieval flow and prints results clearly.
    """
    print(f"\n{'='*50}")
    print(f"Running Hierarchical Retrieval")
    print(f"Query: {query}")
    print(f"Mode: {mode}")
    print(f"{'='*50}")

    results = mode_router.handle_query(storage.supabase, query, mode)

    if mode == "id_only":
        # Minimal output for id_only mode
        if results == "Not Found" or not results:
            print("No relevant document found.")
        elif isinstance(results, str):
            print(results)
        else:
            # Fallback for old list-of-dicts format
            print(f"  Found {len(results)} relevant source(s):")
            for res in results:
                print(f"  - Document ID: {res['document_id']}")
                print(f"    Section: {res['section_title']}")
        return # Skip the decorative footer for id_only

    print(f"\n{'='*20} RETRIEVAL RESULTS {'='*20}")
    
    if results == "Not Found" or not results:
        print("  [!] No relevant results found for your query.")
    elif mode == "explain":
        print(f"\n--- SLM EXPLANATION ---")
        # Removing risky sys.stdout = io.TextIOWrapper redefinition
        # Instead, we just print normally. Modern Python 3 handles this better.
        try:
            print(results)
        except UnicodeEncodeError:
            # Fallback for older/misconfigured Windows terminals
            print(results.encode('ascii', 'replace').decode('ascii'))
        print(f"----------------------")
    
    print(f"{'='*50}\n")
    return results

def run_interactive_loop(mode):
    """
    Starts an interactive chat loop for follow-up questions.
    """
    print(f"\n{'='*50}")
    print(f"Entering Interactive Chat Mode (Mode: {mode})")
    print(f"Type 'exit' or 'quit' to end the session.")
    print(f"{'='*50}")

    chat_history = []
    
    while True:
        try:
            query = input("\nUser: ").strip()
            if query.lower() in ["exit", "quit"]:
                print("Exiting interactive mode...")
                break
            
            if not query:
                continue

            # Run retrieval flow with history
            results = mode_router.handle_query(storage.supabase, query, mode, chat_history)
            
            # Print results (handling display logic similar to run_retrieval_flow)
            if mode == "explain":
                print(f"\n--- Assistant ---")
                try:
                    print(results)
                except UnicodeEncodeError:
                    print(results.encode('ascii', 'replace').decode('ascii'))
                print(f"-----------------")
            else:
                print(f"\nAssistant: {results}")

            # Update history
            chat_history.append({"role": "user", "content": query})
            chat_history.append({"role": "assistant", "content": str(results)})

            # Limit history size to 2 exchanges (4 messages) to prevent context bloat
            if len(chat_history) > 4:
                chat_history = chat_history[-4:]

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"\nError in chat loop: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hierarchical RAG Prototype - Ingestion & Retrieval")
    
    # Ingestion Argument
    parser.add_argument("document_path", nargs="?", help="Path to document for ingestion")
    
    # Retrieval Arguments
    parser.add_argument("--query", "-q", help="Semantic query for retrieval")
    parser.add_argument("--mode", "-m", choices=["id_only", "explain"], default="id_only", help="Retrieval mode (default: id_only)")
    parser.add_argument("--interactive", "-i", action="store_true", help="Enter interactive chat mode")

    args = parser.parse_args()

    if args.interactive:
        run_interactive_loop(args.mode)
    elif args.query:
        # 1. Retrieval Mode
        run_retrieval_flow(args.query, args.mode)
    elif args.document_path:
        # 2. Ingestion Mode
        run_ingestion_pipeline(args.document_path)
    else:
        parser.print_help()

