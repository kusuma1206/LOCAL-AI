import sys
sys.path.append('.')
from retrieval.mode_router import detect_query_intent

tests = [
    "Give me an overview of the system",
    "Can you summarize the document?",
    "Please describe the setup.",
    "I need you to explain architecture.",
    "provide a full explanation.",
    "What is the Similarity Gate?",
    "How does Layer 2 work?"
]

for t in tests:
    print(f"'{t}' -> {detect_query_intent(t)}")
