-- FINAL FIX: Ensures match_sections ONLY returns sections that have chunks in the NOLLM table.
-- Run this in your Supabase SQL Editor.

CREATE OR REPLACE FUNCTION public.match_sections (
  query_embedding vector(384),
  match_count int,
  document_ids text[] DEFAULT NULL
)
RETURNS TABLE (
  id bigint,
  document_id uuid,
  section_title text,
  section_summary text,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    s.id,
    s.document_id::uuid,
    s.section_title,
    s.section_summary,
    1 - (s.section_embedding <=> query_embedding) AS similarity
  FROM sections s
  WHERE (document_ids IS NULL OR s.document_id::text = ANY(document_ids))
    -- CRITICAL: Only retrieve sections that have chunks in document_chunks
    AND EXISTS (
      SELECT 1 FROM document_chunks dc 
      WHERE dc.section_id = s.id
    )
  ORDER BY s.section_embedding <=> query_embedding
  LIMIT match_count;
END;
$$;
