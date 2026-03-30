-- Migration: Add status and storage_url to documents table
ALTER TABLE documents 
ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'uploading',
ADD COLUMN IF NOT EXISTS storage_url TEXT;

-- Update existing documents to 'complete' if they have content
UPDATE documents SET status = 'complete' WHERE document_summary IS NOT NULL;
