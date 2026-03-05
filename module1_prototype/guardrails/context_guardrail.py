class ContextGuardrail:
    """
    Guardrail for ensuring integrated context is relevant and safe.
    """
    def __init__(self, max_chunks: int = 5, max_tokens: int = 2000):
        self.max_chunks = max_chunks
        self.max_tokens = max_tokens

    def estimate_tokens(self, text: str) -> int:
        """
        Estimates the number of tokens in a string.
        A rough rule of thumb is 4 characters per token for English text.
        
        Args:
            text (str): The text to estimate tokens for.
            
        Returns:
            int: The estimated number of tokens.
        """
        if not text:
            return 0
        return len(text) // 4

    def limit_context(self, chunks: list, max_chunks: int = None, max_tokens: int = None) -> list:
        """
        Limits the number of chunks and total token count for the LLM context.
        
        Args:
            chunks (list): A list of chunks (dictionaries or strings).
            max_chunks (int, optional): Maximum number of chunks to return.
            max_tokens (int, optional): Maximum estimated tokens allowed.
            
        Returns:
            list: The filtered list of chunks.
        """
        _max_chunks = max_chunks if max_chunks is not None else self.max_chunks
        _max_tokens = max_tokens if max_tokens is not None else self.max_tokens
        
        filtered_chunks = []
        current_token_count = 0
        
        # 1. First, apply chunk count limit
        limited_by_count = chunks[:_max_chunks]
        
        # 2. Then, apply token count limit
        for chunk in limited_by_count:
            # Handle chunk as dictionary with 'content' or as a string
            content = chunk.get('content', '') if isinstance(chunk, dict) else str(chunk)
            chunk_tokens = self.estimate_tokens(content)
            
            if current_token_count + chunk_tokens <= _max_tokens:
                filtered_chunks.append(chunk)
                current_token_count += chunk_tokens
            else:
                print(f"ContextGuardrail: Token limit reached ({current_token_count}). Skipping remaining chunks.")
                break
                
        return filtered_chunks
