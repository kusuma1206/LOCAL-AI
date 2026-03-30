import sys
sys.path.append('.')
from processing.chunker import chunk_text

sections = [
    {
        "section_title": "Layer 1: Similarity Gate",
        "content": "The Similarity Gate validates user queries against trusted knowledge sources before allowing the AI model to process them. " \
                   "It ensures that only queries with a high semantic match to verified documents proceed. " \
                   "If a query falls below the threshold, it is automatically rejected, providing a predefined fallback response. " \
                   "This is the first and most critical layer of the Zero-Trust architecture, serving as a deterministic firewall. " \
                   "By blocking irrelevant or malicious queries early, the system saves computational resources and guarantees safety. " \
                   "The underlying mechanism relies on cosine similarity between the embedded user query and the vectorized document summaries. " \
                   "Administrators can configure the strictness of this gate by adjusting the similarity threshold in the system settings. " \
                   "A typical threshold is set to 0.65, balancing strict adherence to facts with conversational flexibility. " \
                   "This layer heavily depends on the quality of the embeddings generated during the ingestion phase. " \
                   "If the embeddings are poor, the gate will falsely reject valid queries or allow hallucinations to pass. " \
                   "Therefore, selecting a robust embedding model is paramount for the Similarity Gate to function optimally. " \
                   "In testing, this single feature reduced hallucinations by over 90 percent compared to unprotected models."
    },
    {
        "section_title": "Empty Section test",
        "content": "  \n  "
    }
]

chunks = chunk_text(sections, chunk_size=50, overlap=10)

print(f"Generated {len(chunks)} chunks:")
for i, c in enumerate(chunks):
    text = c['chunk_text']
    words = len(text.split())
    print(f"\n--- Chunk {i+1} ({words} words) ---")
    print(text)
