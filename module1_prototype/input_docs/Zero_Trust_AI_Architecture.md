# Sakhi Zero-Trust AI Architecture

This document outlines the implementation of the Zero-Trust security layers for the Sakhi medical assistant. The goal is to eliminate LLM hallucinations and ensure that all medical advice is strictly derived from verified doctor-approved knowledge bases.

## 🛡️ The 4-Layer Defense System

The architecture is built on the principle of **"Verify Everything, Trust Nothing."**

### Layer 1: The Similarity Gate (Deterministic Entrance)
**File:** `main.py` (Lines 457-470)
Before any user query is allowed to reach the Language Model (LLM), it must pass a semantic similarity test.
*   **Threshold:** 0.65 (Cosine Similarity)
*   **Logic:** If the RAG (Retrieval-Augmented Generation) engine cannot find a piece of knowledge in our database with at least 65% relevance to the query, the process is blocked.
*   **Result:** Prevents the AI from answering out-of-scope or unverified medical questions.

### Layer 2: The "Straightjacket" Prompt (Strict Extraction)
**File:** `modules/sakhi_prompt.py`
The LLM's system instructions have been refactored to limit its generative capabilities.
*   **Persona:** Defined as an **Information Extractor**, not a general AI.
*   **Constraint:** Explicitly forbidden from using internal training data for facts.
*   **Fallback:** Forced to use specific fallback phrases if the context is insufficient.

### Layer 3: Real-Time Token Auditor (The Firewall)
**File:** `modules/auditor.py` & `main.py`
This is the "Speed Demon" of the pipeline, providing real-time protection against hallucinations.
*   **Algorithm:** **Aho-Corasick Deterministic String Matching**.
*   **Process:** 
    1.  The Auditor builds a search-trie of approved medical nouns from the RAG context on-the-fly.
    2.  As the LLM streams tokens (SSE), the Auditor stems and verifies every word.
    3.  If an unverified medical noun appears in the stream, the system **instantly aborts the connection**.
*   **Latency:** < 10ms (Negligible impact on Time To First Token).

### Layer 4: Asynchronous Flywheel (Infinite Learning)
**File:** `modules/flywheel.py`
A background logging system that turns failures into knowledge.
*   **Logging:** Every Gate Block (Layer 1) and Auditor Kill (Layer 3) is logged to Supabase (`sakhi_knowledge_flywheel`).
*   **Non-Blocking:** Uses `asyncio.create_task` to ensure user experience isn't slowed down by database writes.
*   **Output:** Generates a weekly "Knowledge Gap" report for the medical team to review and add new content to the vector DB.

---

## 🚀 Technical Stack
*   **Search:** Aho-Corasick (via `pyahocorasick`)
*   **Preprocessing:** NLTK PorterStemmer
*   **Streaming:** FastAPI `StreamingResponse` + SSE (Server-Sent Events)
*   **Logging:** Supabase / PostgreSQL

## 🛠️ Maintenance & Operations
To maintain the integrity of the Zero-Trust system:
1.  **Weekly Audit:** Review the `sakhi_knowledge_flywheel` table.
2.  **Threshold Tuning:** The 0.85 similarity gate can be adjusted in `main.py` based on performance.
3.  **Stemmer Updates:** The whitelist in `modules/auditor.py` should be updated as Sakhi's conversational range grows.

---
*Created by Antigravity AI - Building Safe & Reliable Medical Intelligence.*
