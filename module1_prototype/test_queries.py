from config import settings

URL = f"{settings.API_BASE_URL}/query"

queries = [
    ("Explain the Sakhi WhatsApp backend overview.", "explain"),
    ("What is the Similarity Gate in Zero Trust AI architecture?", "technical"),
    ("what is similarity gate in sakhi zero trust ai archietcture", "explain"), # Forced explain to test override
    ("Who are you?", "technical")
]

for i, (q, mode) in enumerate(queries, 1):
    # The mode is now explicitly defined in the queries list, so the router decision logic is removed here.
    payload = {"query": q, "mode": mode}
    try:
        response = requests.post(URL, json=payload, timeout=120)
        data = response.json()
        with open("test_results_utf8.txt", "w" if i == 1 else "a", encoding="utf-8") as f:
            f.write(f"--- EXAMPLE {i} ---\n")
            f.write(f"User Query: {q}\n\n")
            
            # We want to show raw chunks + final answer. The API returns `result` dict from `handle_query`.
            res = data.get("result", {})
            if isinstance(res, str):
                f.write(f"Error or Blocked: {res}\n")
                continue
                
            chunks = res.get("retrieved_context", [])
            
            f.write("Retrieved context items (before formatting):\n")
            for c in chunks:
                f.write(f"- Type: {c.get('type')}\n")
                content = c.get('content', '')
                f.write(f"  Content snippet: {content[:150]}...\n")
                
            f.write("\nFinal Formatted Answer:\n")
            f.write(res.get("formatted_answer", "No formatted answer") + "\n")
            f.write("\n" + "="*50 + "\n\n")
        
    except Exception as e:
        print(f"Error on query {i}: {e}")
