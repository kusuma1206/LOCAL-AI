-- 1. DROP old versions of match_sections to resolve overloading
-- We try to drop all variations that might exist
DROP FUNCTION IF EXISTS public.match_sections(vector, int, text[]);
DROP FUNCTION IF EXISTS public.match_sections(vector, int, uuid[]);
DROP FUNCTION IF EXISTS public.match_sections(vector, int, name[]);

-- 2. RE-CREATE the correct version (integer doc_ids)
CREATE OR REPLACE FUNCTION public.match_sections (
  query_embedding vector(384),
  match_count int,
  document_ids int[] DEFAULT NULL
)
RETURNS TABLE (
  id bigint,
  doc_id int,
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
    s.doc_id,
    s.section_title,
    s.section_summary,
    1 - (s.section_embedding <=> query_embedding) AS similarity
  FROM sections s
  WHERE (document_ids IS NULL OR s.doc_id = ANY(document_ids))
    AND EXISTS (
      SELECT 1 FROM document_chunks dc 
      WHERE dc.section_id = s.id
    )
  ORDER BY s.section_embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- 3. Also ENSURE match_chunks isn't overloaded
DROP FUNCTION IF EXISTS public.match_chunks(vector, int, uuid[]);
DROP FUNCTION IF EXISTS public.match_chunks(vector, int, text[]);

CREATE OR REPLACE FUNCTION public.match_chunks (
  query_embedding vector(384),
  match_count int,
  section_ids bigint[] DEFAULT NULL
)
RETURNS TABLE (
  content text,
  section_id bigint,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    dc.content,
    dc.section_id,
    1 - (dc.embedding <=> query_embedding) AS similarity
  FROM document_chunks dc
  WHERE (section_ids IS NULL OR dc.section_id = ANY(section_ids))
  ORDER BY dc.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;
