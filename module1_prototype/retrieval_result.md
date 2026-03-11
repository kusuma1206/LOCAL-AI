# The 4-Layer Defense System

💡 Key Insight
The architecture is built on the principle of "Verify Everything, Trust Nothing."

## Core Components

[🛡️ The 4-Layer Defense System]

Layer 1: The Similarity Gate (Deterministic Entrance) File: `main.py` (Lines 457-470) Before any user query is allowed to reach the Language Model (LLM), it must pass a semantic similarity test. • Threshold: 0.65 (Cosine Similarity)
• Logic: If the RAG (Retrieval-Augmented Generation) engine cannot find a piece of knowledge in our database with at least 65% relevance to the query, the process is blocked. • Result: Prevents the AI from answering out-of-scope or unverified medical questions.

Layer 2: The "Straightjacket" Prompt (Strict Extraction) File: `modules/sakhi_prompt.py` The LLM's system instructions have been refactored to limit its generative capabilities. • Persona: Defined as an Information Extractor, not a general AI. • Constraint: Explicitly forbidden from using internal training data for facts. • Fallback: Forced to use specific fallback phrases if the context is insufficient.

The **architecture** is built on the principle of "Verify Everything, **Trust** Nothing."

Layer 3: Real-Time Token Auditor (The Firewall) File: `modules/auditor.py` & `main.py` This is the "Speed Demon" of the pipeline, providing real-time protection against hallucinations. • Algorithm: Aho-Corasick Deterministic String Matching. • Process:

---

📂 Source

Document: Zero_Trust_AI_Architecture.md
Document ID: 7
