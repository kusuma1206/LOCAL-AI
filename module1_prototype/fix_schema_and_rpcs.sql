-- Migration: Fix schema mismatch and update RPCs for UUID support
-- 1. Add missing columns to documents table
ALTER TABLE documents 
ADD COLUMN IF NOT EXISTS document_summary TEXT,
ADD COLUMN IF NOT EXISTS document_embedding vector(384);

-- 2. Add missing columns to sections table
ALTER TABLE sections 
ADD COLUMN IF NOT EXISTS section_summary TEXT;

-- 3. Update match_documents RPC
CREATE OR REPLACE FUNCTION public.match_documents (
  query_embedding vector(384),
  match_count int
)
RETURNS TABLE (
  doc_id int,
  filename text,
  title text,
  document_summary text,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    d.doc_id,
    d.filename,
    d.title,
    d.document_summary,
    1 - (d.document_embedding <=> query_embedding) AS similarity
  FROM documents d
  WHERE d.document_embedding IS NOT NULL
  ORDER BY d.document_embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- 4. Update match_sections to use UUID for section_id and include summary
CREATE OR REPLACE FUNCTION public.match_sections (
  query_embedding vector(384),
  match_count int,
  document_ids int[] DEFAULT NULL
)
RETURNS TABLE (
  section_id uuid,
  doc_id int,
  title text,
  section_summary text,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    s.section_id,
    s.doc_id,
    s.title,
    s.section_summary,
    1 - (s.section_embedding <=> query_embedding) AS similarity
  FROM sections s
  WHERE (document_ids IS NULL OR s.doc_id = ANY(document_ids))
    AND EXISTS (
      SELECT 1 FROM document_chunks dc 
      WHERE dc.section_id = s.section_id
    )
  ORDER BY s.section_embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- 5. Update match_chunks to use UUID for section_id
CREATE OR REPLACE FUNCTION public.match_chunks (
  query_embedding vector(384),
  match_count int,
  section_ids uuid[] DEFAULT NULL
)
RETURNS TABLE (
  chunk_id uuid,
  content text,
  section_id uuid,
  similarity float,
  chunk_index int
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    dc.chunk_id,
    dc.content,
    dc.section_id,
    1 - (dc.embedding <=> query_embedding) AS similarity,
    dc.chunk_index
  FROM document_chunks dc
  WHERE (section_ids IS NULL OR dc.section_id = ANY(section_ids))
  ORDER BY dc.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;
