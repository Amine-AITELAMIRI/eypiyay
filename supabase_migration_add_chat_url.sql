-- Migration: Add chat_url field for follow-up system
-- This allows clients to continue conversations in existing ChatGPT chats

-- Add chat_url column
ALTER TABLE requests ADD COLUMN IF NOT EXISTS chat_url TEXT;

-- Add follow_up_chat_url column (for tracking which chat was used)
ALTER TABLE requests ADD COLUMN IF NOT EXISTS follow_up_chat_url TEXT;

-- Create index for better performance when querying by chat_url
CREATE INDEX IF NOT EXISTS idx_requests_chat_url ON requests(chat_url);

-- Success message
SELECT 'Follow-up system migration completed successfully!' as message;

