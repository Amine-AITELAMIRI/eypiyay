-- ChatGPT Relay - Supabase Database Schema
-- Run this in Supabase SQL Editor: https://app.supabase.com/project/hizcmicfsbirljnfaogr/sql

-- Create requests table
CREATE TABLE IF NOT EXISTS requests (
    id BIGSERIAL PRIMARY KEY,
    prompt TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    response TEXT,
    error TEXT,
    worker_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    webhook_url TEXT,
    webhook_delivered BOOLEAN NOT NULL DEFAULT FALSE,
    prompt_mode TEXT,
    model_mode TEXT
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_requests_status ON requests(status);
CREATE INDEX IF NOT EXISTS idx_requests_created_at ON requests(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_requests_updated_at ON requests(updated_at DESC);

-- Create a function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
DROP TRIGGER IF EXISTS update_requests_updated_at ON requests;
CREATE TRIGGER update_requests_updated_at
    BEFORE UPDATE ON requests
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security (RLS)
ALTER TABLE requests ENABLE ROW LEVEL SECURITY;

-- Create policy to allow service_role full access
CREATE POLICY "Enable full access for service_role" ON requests
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Optional: Create policy for authenticated users to read their own requests
-- Uncomment if you want to add user authentication later
-- CREATE POLICY "Users can view all requests" ON requests
--     FOR SELECT
--     TO authenticated
--     USING (true);

-- Grant permissions
GRANT ALL ON requests TO service_role;
GRANT USAGE, SELECT ON SEQUENCE requests_id_seq TO service_role;

-- Success message
SELECT 'Database schema created successfully!' as message;

