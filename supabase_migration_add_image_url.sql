-- Migration: Add image_url column to requests table
-- Run this in Supabase SQL Editor if you already have the requests table
-- https://app.supabase.com/project/hizcmicfsbirljnfaogr/sql

-- Add image_url column to requests table
ALTER TABLE requests ADD COLUMN IF NOT EXISTS image_url TEXT;

-- Verify the column was added
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'requests' 
ORDER BY ordinal_position;

-- Success message
SELECT 'Successfully added image_url column to requests table!' as message;

