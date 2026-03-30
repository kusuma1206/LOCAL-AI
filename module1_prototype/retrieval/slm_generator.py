import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

class SLMGenerator:
    _instance = None
    _model = None
    _tokenizer = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SLMGenerator, cls).__new__(cls)
        return cls._instance

    def _load_model(self):
        # Helper for Windows-safe prints
        def _safe_print(text):
            try:
                print(text)
            except UnicodeEncodeError:
                import sys
                print(text.encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding))

        self._safe_print = _safe_print

        if self._model is None:
            model_id = "rd211/Qwen3-0.6B-Instruct" # Updated repo id
            print(f"  [SLM Generator] Loading model: {model_id}...")
            
            self._tokenizer = AutoTokenizer.from_pretrained(model_id)
            
            # Using float16 if GPU is available, else default
            torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
            
            # For a 0.6B model, we avoid device_map="auto" to prevent slow offloading logic
            device = "cuda" if torch.cuda.is_available() else "cpu"
            print(f"  [SLM Generator] Target device: {device}")
            
            self._model = AutoModelForCausalLM.from_pretrained(
                model_id,
                dtype=torch_dtype,
                low_cpu_mem_usage=True,
                trust_remote_code=True
            ).to(device)
            
            print(f"  [SLM Generator] Model loaded successfully on {device}.")

    def sanitize_context(self, context: str) -> str:
        """
        Sanitize Retrieved Context: Removes exam-like patterns and LaTeX artifacts.
        """
        patterns_to_remove = [
            "Possible Answers:",
            "Answer:",
            "Final Answer:",
            "\\boxed",
            "Reasoning:",
        ]

        for p in patterns_to_remove:
            context = context.replace(p, "")

        return context

    @torch.inference_mode()
    def generate_explanation(self, query: str, context_chunks: list[str], chat_history: list[dict] = None, retrieval_metadata: dict = None) -> tuple[str, dict]:
        self._load_model()
        
        print(f"  [SLM Generator] Context chunks received: {len(context_chunks)}")
        total_context_len = sum(len(c) for c in context_chunks)
        print(f"  [SLM Generator] Total context length: {total_context_len} characters")
        
        concatenated_chunks = "\n\n".join(context_chunks)
        concatenated_chunks = self.sanitize_context(concatenated_chunks)
        
        print("=== CONTEXT TO SLM ===")
        self._safe_print(concatenated_chunks)
        print("======================")
        
        # Build chat history string
        history_str = ""
        if chat_history:
            history_str = "\n\nConversation So Far:\n"
            for msg in chat_history:
                role = "User" if msg["role"] == "user" else "Assistant"
                history_str += f"{role}: {msg['content']}\n"
        
        # Completion-Style Anchor Prompt
        prompt = f"""
[SYSTEM DATA]
Role: Expert Technical Mentor. 

STRICT FORMATTING SCHEMA (V4.1):
1. Use Markdown headings (## or ###) for all sections. NEVER number a heading.
2. Every label (File, Persona, Threshold, Algorithm, Process, Logging, Output, Constraint, Latency, etc.) MUST use the exact format: **Label:** description.
3. The explanation MUST be on the SAME LINE as the label. Never split across lines.
4. Always wrap file paths in inline code format: **File:** `modules/auditor.py`.
5. Technical blocks (Process, Algorithm, Logging, Configuration, Output) MUST use bullet points (*).
6. Numbered lists (1., 2.) are FORBIDDEN unless explaining a chronological step-by-step procedure.

[NEGATIVE EXAMPLES - DO NOT DO THIS]
- Do NOT split lines: 
  **Persona:**
  Defined as an Information Extractor (WRONG)
- Do NOT number processes:
  **Process**
  1. Step one (WRONG)
- Do NOT bullet headers:
  * **Algorithm:** (WRONG if it's a section header)

[OUTPUT VALIDATION]
Verify: No numbered headings, all labels follow **Label:** format on a single line, file names have backticks, and process steps use bullets. Rewrite if any rule is violated.

Context:
{concatenated_chunks}
{history_str}

[QUESTION]
{query}

[EXPERT RESPONSE]
<result>
## Executive Summary
"""

        import time
        t_gen_start = time.time()
        
        # Token counting for diagnostics
        system_prompt = prompt.split("Context:")[0]
        context_str = concatenated_chunks
        user_query_part = f"\n[QUESTION]\n{query}"
        
        sys_tokens = len(self._tokenizer.encode(system_prompt))
        ctx_tokens = len(self._tokenizer.encode(context_str))
        query_tokens = len(self._tokenizer.encode(user_query_part))
        
        # Direct tokenization for plain prompt
        print(f"  [SLM Generator] Tokenizing prompt...")
        model_inputs = self._tokenizer([prompt], return_tensors="pt").to(self._model.device)
        total_prompt_tokens = model_inputs["input_ids"].shape[1]
        
        print(f"  [SLM Generator] Starting hyper-detailed completion (max_new_tokens=550)...")
        generated_ids = self._model.generate(
            input_ids=model_inputs["input_ids"],
            attention_mask=model_inputs["attention_mask"],
            max_new_tokens=550,
            do_sample=False,
            repetition_penalty=1.1, 
            no_repeat_ngram_size=3,
            use_cache=True,
            pad_token_id=self._tokenizer.eos_token_id,
            eos_token_id=self._tokenizer.eos_token_id
        )
        
        gen_time = time.time() - t_gen_start
        generated_tokens_count = len(generated_ids[0]) - model_inputs["input_ids"].shape[1]
        tokens_per_second = generated_tokens_count / gen_time if gen_time > 0 else 0
        
        # Diagnostic Report
        device_type = self._model.device.type
        backend = "Transformers (HuggingFace)"
        
        print("\n================ LLM DIAGNOSTIC REPORT ================")
        print(f"Model: {self._tokenizer.name_or_path if hasattr(self._tokenizer, 'name_or_path') else 'Unknown'}")
        print(f"Backend: {backend}")
        print(f"Hardware: {device_type.upper()}")
        print(f"\nSystem prompt tokens: {sys_tokens}")
        print(f"Context tokens: {ctx_tokens}")
        print(f"User query tokens: {query_tokens}")
        print(f"Total prompt tokens: {total_prompt_tokens}")
        
        if retrieval_metadata:
            print(f"\nDocuments retrieved: {retrieval_metadata.get('num_documents', 0)}")
            print(f"Sections retrieved: {retrieval_metadata.get('num_sections', 0)}")
            print(f"Chunks retrieved: {retrieval_metadata.get('num_chunks', 0)}")
            scores = retrieval_metadata.get('chunk_scores', [])
            if scores:
                top_scores = sorted(scores, reverse=True)[:3]
                print(f"Top Similarity Scores: {', '.join([f'{s:.4f}' for s in top_scores])}")
        
        print(f"\nContext characters: {total_context_len}")
        print(f"Estimated context tokens: {ctx_tokens}")
        
        print(f"\nGenerated tokens: {generated_tokens_count}")
        print(f"Generation time: {gen_time:.2f} seconds")
        print(f"Tokens per second: {tokens_per_second:.2f}")
        
        print(f"\nmax_tokens: 550")
        print(f"temperature: 0.0 (do_sample=False)")
        print(f"top_p: N/A (Greedy)")
        print(f"streaming: disabled")
        print("======================================================\n")

        print("-" * 30)
        
        # Decode and strictly clean the output
        decoded_output = self._tokenizer.decode(generated_ids[0], skip_special_tokens=True)

        # Extraction logic for completion-style anchor
        if "<result>" in decoded_output:
            response = decoded_output.split("<result>")[-1].split("</result>")[0].strip()
            if not response.startswith("##"):
                response = "## Executive Summary\n" + response
        else:
            response = decoded_output.replace(prompt, "").strip()
            if not response.startswith("##"):
                response = "## Executive Summary\n" + response
        
        # Hard cut markers
        stop_markers = [
            "Final Answer", "\\boxed", "Possible Answers", "Answer:", "Alright,",
            "Wrapping up", "covers everything", "Now I need to check", "solid overview",
            "confidence this provides", "**End of Response**", "thinking process",
            "Hmm, okay", "let me check", "That makes sense"
        ]

        for marker in stop_markers:
            if marker in response:
                response = response.split(marker)[0]

        response = response.strip()

        # Sentence completion logic
        if response and not response.endswith((".", "!", "?", "]", ")", "*")):
            last_period = response.rfind(".")
            if last_period != -1:
                response = response[:last_period + 1]
            response = response.strip()

        # Output Guardrails
        t_val_start = time.time()
        print("SLM response completed. Applying output guardrails...")
        
        if "Information not found in documents" in response or "not mentioned" in response.lower():
            response = "Information not found in the documents."
        else:
            from .guardrails import guardrail_engine
            response = guardrail_engine.validate_output(response)
        
        val_time = time.time() - t_val_start
        
        timings = {
            "llm_generation": gen_time,
            "output_validation": val_time
        }
        
        return response, timings

# Singleton access
generator = SLMGenerator()

def generate_explanation(query: str, context_chunks: list[str], chat_history: list[dict] = None, retrieval_metadata: dict = None) -> tuple[str, dict]:
    return generator.generate_explanation(query, context_chunks, chat_history, retrieval_metadata)

