-- Migration: Add chunk_index and is_heading to document_chunks
-- This enables sequential retrieval and heading-aware expansion.

ALTER TABLE document_chunks 
ADD COLUMN IF NOT EXISTS chunk_index INT,
ADD COLUMN IF NOT EXISTS is_heading BOOLEAN DEFAULT FALSE;

-- Update match_chunks RPC to return these new fields
CREATE OR REPLACE FUNCTION public.match_chunks (
  query_embedding vector(384),
  match_count int,
  section_ids bigint[] DEFAULT NULL
)
RETURNS TABLE (
  content text,
  section_id bigint,
  similarity float,
  chunk_index int,
  is_heading boolean
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    dc.content,
    dc.section_id,
    1 - (dc.embedding <=> query_embedding) AS similarity,
    dc.chunk_index,
    dc.is_heading
  FROM document_chunks dc
  WHERE (section_ids IS NULL OR dc.section_id = ANY(section_ids))
  ORDER BY dc.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;
