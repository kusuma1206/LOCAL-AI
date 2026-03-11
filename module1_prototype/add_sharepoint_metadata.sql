-- Migration: Add SharePoint and User metadata to documents table
-- This script adds tracking columns for cloud storage and user auditing.

ALTER TABLE documents 
ADD COLUMN IF NOT EXISTS title TEXT,
ADD COLUMN IF NOT EXISTS sharepoint_url TEXT,
ADD COLUMN IF NOT EXISTS sharepoint_file_id TEXT,
ADD COLUMN IF NOT EXISTS uploaded_by TEXT,
ADD COLUMN IF NOT EXISTS upload_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;

-- Add comment for documentation
COMMENT ON COLUMN documents.sharepoint_url IS 'Direct link to the document in SharePoint';
COMMENT ON COLUMN documents.sharepoint_file_id IS 'Unique identifier from Microsoft Graph API';
