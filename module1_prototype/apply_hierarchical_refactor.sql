-- 1. ADD doc_id to sections table
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='sections' AND column_name='doc_id') THEN
        ALTER TABLE sections ADD COLUMN doc_id int4;
    END IF;
END $$;

-- 2. POPULATE sections.doc_id from documents.doc_id
UPDATE sections s
SET doc_id = d.doc_id
FROM documents d
WHERE s.document_id = d.id;

-- 3. CREATE match_documents RPC
CREATE OR REPLACE FUNCTION public.match_documents (
  query_embedding vector(384),
  match_count int
)
RETURNS TABLE (
  doc_id int,
  filename text,
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
    d.document_summary,
    1 - (d.document_embedding <=> query_embedding) AS similarity
  FROM documents d
  WHERE d.document_embedding IS NOT NULL
  ORDER BY d.document_embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- 4. UPDATE match_sections to use integer doc_id filtering
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

-- 5. ENSURE match_chunks exists and uses bigint for section_filter
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
