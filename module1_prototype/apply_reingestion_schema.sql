-- Migration: Add file_hash and unique constraint to documents table
-- Supports V4 Re-ingestion System

-- 1. Add file_hash column
ALTER TABLE documents 
ADD COLUMN IF NOT EXISTS file_hash TEXT;

-- 2. Add unique constraint on filename to prevent bypass
-- Note: We use filename as the primary unique identifier as per Step 8.
-- However, we also use file_hash for content-based detection.
ALTER TABLE documents
ADD CONSTRAINT unique_file_name UNIQUE (filename);

-- 3. Create a query log for replacement events (as per Step 9)
CREATE TABLE IF NOT EXISTS ingestion_logs (
    id BIGSERIAL PRIMARY KEY,
    event TEXT NOT NULL,
    file_name TEXT NOT NULL,
    old_document_id INT,
    new_document_id INT,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB
);
