import sys
import uuid
sys.path.append('.')
from processing.storage import insert_document_chunk, supabase

section_id = str(uuid.uuid4())
embedding = [0.0] * 384  # vector(384) dummy
chunk_id = insert_document_chunk(supabase, section_id, "Layer 1: Similarity Gate...", embedding, 1)
print(f"Inserted chunk with ID: {chunk_id}")
