-- SQL to create query_logs table in Supabase

create table if not exists public.query_logs (
    id uuid default gen_random_uuid() primary key,
    query text not null,
    mode text not null,
    retrieved_section_ids jsonb,
    retrieved_chunk_ids jsonb,
    similarity_scores jsonb,
    generation_time_ms integer,
    response_text text,
    timestamp timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Enable Row Level Security (optional but recommended for production)
-- alter table public.query_logs enable row level security;
