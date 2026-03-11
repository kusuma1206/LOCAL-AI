-- Migration: Add structured semantic metadata to document_chunks
-- Provides awareness of the document and section at the chunk level.

ALTER TABLE document_chunks 
ADD COLUMN IF NOT EXISTS document_id int4,
ADD COLUMN IF NOT EXISTS document_name text,
ADD COLUMN IF NOT EXISTS section_title text,
ADD COLUMN IF NOT EXISTS parent_section text;

-- Update match_chunks RPC to return these new fields
DROP FUNCTION IF EXISTS public.match_chunks(vector(384), integer, bigint[]);

CREATE OR REPLACE FUNCTION public.match_chunks (
  query_embedding vector(384),
  match_count int,
  section_ids bigint[] DEFAULT NULL
)
RETURNS TABLE (
  id bigint,
  content text,
  section_id bigint,
  similarity float,
  chunk_index int,
  is_heading boolean,
  document_id int4,
  document_name text,
  section_title text,
  parent_section text
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    dc.id,
    dc.content,
    dc.section_id,
    1 - (dc.embedding <=> query_embedding) AS similarity,
    dc.chunk_index,
    dc.is_heading,
    dc.document_id,
    dc.document_name,
    dc.section_title,
    dc.parent_section
  FROM document_chunks dc
  WHERE (section_ids IS NULL OR dc.section_id = ANY(section_ids))
  ORDER BY dc.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;
