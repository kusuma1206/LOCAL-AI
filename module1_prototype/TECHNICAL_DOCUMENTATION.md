# TECHNICAL DOCUMENTATION: SLM RAG SYSTEM

## 1. PROJECT OVERVIEW
- **Project name:** Technical Assistant (SLM RAG Platform)
- **Purpose of the project:** To provide a highly accurate, deterministic, and strict "Zero-Trust" intelligent technical mentor and retrieval system that can accurately answer queries based solely on ingested documents.
- **Problem it solves:** Prevents LLM hallucinations using strict guardrails and hierarchical retrieval. It solves the problem of returning unreliable or out-of-scope answers by heavily constraining the generative model and enforcing rigid retrieval standards.
- **Real-world use case:** A chatbot (or web interface) where users can upload complex technical documents (like architecture docs, medical guidelines, or API specs) and chat with them safely and accurately.
- **Target users:** Developers, researchers, or domain experts who need reliable, exact answers from a predefined corpus of knowledge without the risk of AI hallucination.

---

## 2. SYSTEM ARCHITECTURE

The system follows a Hierarchical Retrieval-Augmented Generation (HRAG) architecture backed by a Small Language Model (SLM) for generation and a Zero-Trust guardrail system.

**High-Level Architecture:**
1. **API Layer:** FastAPI backend exposing web endpoints for querying and document uploading.
2. **Ingestion Pipeline:** A robust multi-stage pipeline that parses, cleans, analyzes, and hierarchically structures documents before vectorization.
3. **Retrieval Pipeline:** A 3-level top-down search (Document -> Section -> Chunk) ensures highly accurate context fetching.
4. **Generation & Guardrail Engine:** A local SLM generates answers from the retrieved context, constantly monitored by proactive stopping criteria and output guardrails.

**Data Flow (Architecture Flow):**
```text
User Query
↓
API Layer (FastAPI endpoint `/query` or `/chat`)
↓
Intent Detection & Query Guardrails (Greet / Out-of-Scope / Tech)
↓
Query Correction & Query Embedding (all-MiniLM-L6-v2)
↓
Retrieval Layer (Hierarchical Faiss/Supabase Search)
   ├─ Level 1: Document Retrieval (Top 3)
   ├─ Level 2: Section Retrieval (Top 3 from docs)
   └─ Level 3: Chunk Retrieval (Top 3 from sections)
↓
Context Assembly (Global Summary + Section Summary + Chunk Detail)
↓
Processing Layer / SLM Generation (Qwen3-0.6B-Instruct on CPU)
↓
Output Validation Guardrails & Cleanup Formatting
↓
User Output
```

---

## 3. TECHNOLOGY STACK

| Technology | Purpose | Why used |
| :--- | :--- | :--- |
| **Python** | Core Programming Language | Ecosystem dominance for AI, text processing, and backend logic. |
| **FastAPI** | REST API Framework | High performance, async support, auto-generated OpenAPI docs. |
| **Supabase (PostgreSQL)** | Primary Database & Vector Store | Combines relational metadata storage with powerful `pgvector` similarity search capabilities. |
| **all-MiniLM-L6-v2** | Text Embedding Model | Fast, lightweight (384-dimensions), highly effective semantic matching. |
| **Qwen3-0.6B-Instruct** | Small Language Model (SLM) | Small footprint model that can run inference on standard CPUs while maintaining strong instruction-following capabilities. |
| **HuggingFace Transformers / PyTorch** | Deep Learning Framework | For loading, tokenizing, and generating text using the SLM locally. |
| **PyMuPDF (`fitz`) & `python-docx`** | Document Parsing | Reliable extraction of raw text from PDFs and Word documents. |
| **FAISS** | In-Memory Vector Cache | Optional local snapshotting of vectors for fast in-memory similarity checks. |

---

## 4. PROJECT FOLDER STRUCTURE

```text
/module1_prototype
├── api.py                   # FastAPI server, route definitions (/query, /chat, /upload)
├── main.py                  # CLI entry point, master ingestion pipeline orchestration pipeline
├── processing/              # Data Ingestion and Processing Modules
│   ├── chunker.py           # Structure-aware chunking logic
│   ├── cleaner.py           # Noise reduction and text normalization
│   ├── embedder.py          # Wrapper for loading all-MiniLM-L6-v2
│   ├── extractor.py         # PyMuPDF/docx logic to pull text from files
│   ├── metadata_builder.py  # Enriches chunks with context (confidence, IDs)
│   ├── section_summarizer.py# Generates summaries for full docs and sections
│   ├── storage.py           # Supabase DB operations (insert, upsert, delete)
│   ├── structure_analyzer.py# Detects headers and document layout
│   └── validator.py         # Validates files, sizes, dupes, and OCR needs
├── retrieval/               # Querying and Generation Modules
│   ├── cache_manager.py     # LRU Cache for exact queries to avoid re-computing
│   ├── mode_router.py       # Main orchestrator for query lifecycle and contextual chat
│   ├── document_retriever.py# Level 1 Retrieval (Documents)
│   ├── section_retriever.py # Level 2 Retrieval (Sections)
│   ├── chunk_retriever.py   # Level 3 Retrieval (Chunks)
│   ├── slm_generator.py     # Qwen3 SLM logic, MetaTalk stopping criteria, formatting
│   ├── guardrails.py        # Zero-Trust checks, similarity thresholding
│   ├── query_embedder.py    # Embeds user queries
│   └── query_preprocessor.py# Corrects typos in queries
├── vector_store/            # Local vector indices (e.g. FAISS snapshots)
├── config/                  # Configuration settings (API keys, chunk sizes)
└── docs/                    # Sample input documents
```

---

## 5. DATA INGESTION PIPELINE

When a document enters the system (via the `/upload` API endpoint or `main.py` CLI), it goes through a rigorous, linear pipeline:

1. **Upload & Validation:** The file is saved locally. `validator.py` checks format compatibility (.pdf, .docx, .md) and scans for scanned-PDFs requiring OCR.
2. **Text Extraction:** `extractor.py` reads page-by-page. A confidence score is calculated based on text density.
3. **Cleaning:** `cleaner.py` strips out excessive whitespaces, newlines, and non-semantic noise.
4. **Structure Analysis:** `structure_analyzer.py` uses NLP heuristic rules to identify physical sections and headers in the text.
5. **Hierarchical Summarization & Embedding:** 
   - A global summary is generated for the entire document and embedded.
   - Summaries are generated for each individual section and embedded.
6. **Chunking & Storage:** The text inside each section is chunked. Vectors are generated for each chunk. The Document, Sections, and Chunks are pushed to Supabase.

---

## 6. CHUNKING STRATEGY

- **Type of chunking used:** Semantic Structure-Aware Chunking.
- **Why this method was chosen:** Standard sliding-window token chunking breaks context mid-sentence and loses track of what header the text belongs to. Structure-aware chunking maintains semantic boundaries.
- **How it works:**
  - Split content strictly on paragraph boundaries (`\n\n`).
  - Anchor chunks by prepending the current section's title to the beginning of the chunk (e.g., `[Overview] This is a paragraph.`).
  - If a paragraph exceeds the size limit, it splits gracefully by sentence boundaries (`. ! ?`).
- **Chunk metrics:** Target chunk size is 500 characters, overlap is roughly 50.
- **Benefits:** Ensures complete, cohesive thoughts chunks mapping accurately to their section titles.
- **Limitations:** Creates highly variable chunk sizes. Very short paragraphs might lack density, requiring the system to rely heavily on the prepended title context.

---

## 7. EMBEDDING GENERATION

- **Embedding model:** `sentence-transformers/all-MiniLM-L6-v2`
- **Why selected:** It is a 384-dimensional model that is extremely fast, uses minimal memory, and offers excellent semantic matching performance compared to arbitrarily large models.
- **Conversion Process:** 
  - For Documents/Sections: The extracted summary string is encoded.
  - For Chunks: The chunk text (with its anchored title) is encoded.
- **Storage format:** Stored as `pgvector` native vectors (`vector(384)`) inside PostgreSQL (Supabase) and locally inside a FAISS flat L2 index (`index.faiss`).

---

## 8. DATABASE / VECTOR STORE

- **Database used:** Supabase (PostgreSQL with `pgvector` extension)
- **Schema:**
  - `documents`: Stores document UUID, `filename`, `document_summary`, `document_embedding`.
  - `sections`: Stores section UUID, `document_id` (FK), `section_title`, `section_summary`, `section_embedding`.
  - `document_chunks`: Stores chunk UUID, `section_id` (FK), `content`, `embedding`, `chunk_hash`.
  - `query_logs`: Audit trail for queries.
- **Indexing Method:** Flat exact nearest neighbor or IVFFlat via `pgvector`. A SHA-256 `chunk_hash` is computed on chunk text to allow idempotent UPSERTs without duplicating data.
- **Search Optimization:** Hierarchical indexing reduces the vector search space from thousands of chunks to just a handful of documents first, then their child sections, then child chunks.

---

## 9. RETRIEVAL PIPELINE

Retrieval is strictly **Hierarchical** to maximize precision and eliminate cross-document hallucination.

**Step-by-Step Flow:**
1. **Query Preprocessing:** Typo correction and Intent Detection (e.g. greets, identity check, out of scope).
2. **Query Embedding:** Query is converted into a 384-dim vector.
3. **Similarity Gate (Guardrail):** Checks overall domain relevance. If max score < 0.65, connection is terminated early.
4. **Level 1 (Document Retrieval):** Finds Top 3 mostly relevant *Documents* globally based on document_embedding.
5. **Level 2 (Section Retrieval):** Zooms into those top documents to find the Top 3 most relevant *Sections* based on section_embedding.
6. **Level 3 (Chunk Retrieval):** Searches only the `document_chunks` belonging to those specific `section_id`s, returning the Top chunks.
7. **Context Assembly:** Creates a concatenated string featuring:
   - Level 1 Global Doc Summary
   - Level 2 Relevant Section Summaries
   - Level 3 Detailed Chunk Text.

---

## 10. RESPONSE GENERATION

- **LLM Used:** Qwen3-0.6B-Instruct (via Huggingface Transformers).
- **Prompting:** Employs a specific context prompt demanding factual synthesis and strictly forbidding exterior knowledge. 
- **Proactive Stopping (`MetaTalkStoppingCriteria`):** Intercepts generation token-by-token. If the model starts producing garbage, meta-talk (e.g., "Let me think about this"), or exceeds a healthy sentence limit, early stopping is triggered.
- **Formatting Layer:** Post-processes SLM output. 
  - Sanitize responses by removing exam patterns (`Final Answer:`).
  - Truncates incomplete tail sentences.
  - Restructures lists to force linebreaks on numbered items.
  - Removes banned marketing fluff words (`cutting-edge`, `robust`).

---

## 11. PERFORMANCE OPTIMIZATION

- **Parallelism Defaults:** FastAPI runs intensive processing via `asyncio.to_thread` preventing main-loop blocking.
- **Hierarchical Search Speed:** Searching 3 documents -> small subset of sections -> small subset of chunks is exponentially faster than searching 10,000 global chunks simultaneously.
- **Caching:** Exact query hits are instantly returned via a local LRU cache (`cache_manager.py`).
- **Token Limits:** The SLM context window is aggressively clamped to ~600-800 tokens max to allow tolerable inference speeds on standard CPUs.

---

## 12. SECURITY AND ACCESS CONTROL

- **Zero-Trust AI Architecture:** The architecture assumes the LLM is a liability. 
- **Data Privacy:** Vector matching runs securely in Supabase. Inference (Qwen SLM) runs entirely **locally based on CPU execution**, meaning no PII/internal documents leak to OpenAI or third-party APIs during the explanation generation phase.
- **Hallucination Firewalls:**
  - Similarity Gate: Blocks queries not matching the DB vector space.
  - Output Guardrails: Scrutinizes the final SLM output.

---

## 13. LIMITATIONS

1. **Context Fragmentation:** Paragraph boundary splitting can occasionally split highly cohesive concepts if authors misused paragraph breaks.
2. **Hierarchical Bottleneck:** If a Document's high-level summary (`document_embedding`) happens to not mathematically align with an extremely niche/specific query, that document is rejected at Level 1, meaning the deeper, highly-relevant chunk will never be found.
3. **CPU Inference Latency:** Generating 400 tokens locally on a CPU for Qwen 0.6B takes significantly longer than API calls to larger cloud models.

---

## 14. FUTURE IMPROVEMENTS

1. **Hybrid Keyword Search (BM25):** Integrating keyword search alongside vector search in Supabase to resolve the hierarchical bottleneck (niche exact-word matches often fail in pure semantic searches).
2. **GPU Acceleration (vLLM/ONNX):** Shifting the SLM from naive Transformers/CPU to ONNX runtime or vLLM to decrease generation latency by 5x-10x.
3. **Cross-Document Synthesis:** Relaxing the strict hierarchical funnel for broader "Compare A and B" type questions.

---

## 15. END-TO-END WORKFLOW (Data to Answer)

1. **Admin File Upload:** User uploads a PDF via POST `/upload`.
2. **Ingestion Engine:** `main.py` extracts text, chunks it, and pushes vectors to Supabase.
3. **User Query POSTed:** User sends "How does caching work?" to POST `/chat`.
4. **Intent & Embed:** `mode_router.py` verifies the intent is TECHNICAL and embeds the query.
5. **Funnel Retrieval:** Supabase is queried > Top Doc found > Top Sections identified > Detailed chunks retrieved.
6. **Prompt Assembly:** Chunks are formatted into a rigid prompt.
7. **Inference Triggered:** Qwen SLM reads the prompt and generates an explanation token by token until criteria tells it to stop.
8. **Cleanup & Delivery:** String manipulation algorithms run, formatting is beautified, and JSON response is sent to the client.

---

## 16. SIMPLE REAL-WORLD EXAMPLE

**User Query:** `"Explain the Sakhi WhatsApp backend architecture."`

1. **Validation & Correction:** System confirms it is a valid technical question. No spelling corrections needed.
2. **Embedding:** The query is encoded into a 384-length float array (`all-MiniLM-L6-v2`).
3. **Document Retrieval (Level 1):** The vector array targets Supabase. It matches the summary of `system_design.md` with an 85% similarity.
4. **Section Retrieval (Level 2):** Inside `system_design.md`, the vectors match the sections `[Overview]` and `[1. High-Level Architecture]`.
5. **Chunk Retrieval (Level 3):** Fetches the exact paragraphs describing `main.py`, FastAPI, and the database schema from the matched sections.
6. **Context Concatenation:** It creates a prompt string: `Context: [1. High-Level Architecture] The system is a Python backend...`
7. **SLM Invocation:** The local Qwen 0.6B model is prompted. It generates: *"The Sakhi WhatsApp backend is a FastAPI-based Python application... 1. It uses Supabase... 2. It implements Zero-Trust..."*
8. **Formatting & Output:** The generator removes any potential trailing stop words, formats the list items nicely with line breaks, logs the latency in `query_logs`, and renders the crisp response back to the user app.
