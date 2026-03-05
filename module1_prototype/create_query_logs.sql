-- SQL Script to create the query_logs table for auditing
-- Run this in the Supabase SQL Editor

CREATE TABLE IF NOT EXISTS public.query_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT now(),
    query TEXT NOT NULL,
    mode TEXT NOT NULL,
    retrieved_section_ids JSONB,
    retrieved_chunk_ids JSONB,
    similarity_scores JSONB,
    generation_time_ms INTEGER,
    response_text TEXT
);

-- Optional: Enable RLS
ALTER TABLE public.query_logs ENABLE ROW LEVEL SECURITY;

-- Optional: Create basic policy to allow inserts (adjust as needed for security)
CREATE POLICY "Allow anonymous insert" ON public.query_logs FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow authenticated select" ON public.query_logs FOR SELECT USING (auth.role() = 'authenticated');
