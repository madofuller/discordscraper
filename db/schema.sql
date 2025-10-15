-- Discord Scraper Database Schema
-- PostgreSQL 12+

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Servers table
CREATE TABLE IF NOT EXISTS servers (
    server_id BIGINT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    icon_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Subnets table
CREATE TABLE IF NOT EXISTS subnets (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    tags TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Channels table
CREATE TABLE IF NOT EXISTS channels (
    channel_id BIGINT PRIMARY KEY,
    server_id BIGINT NOT NULL REFERENCES servers(server_id) ON DELETE CASCADE,
    subnet_id INTEGER REFERENCES subnets(id) ON DELETE SET NULL,
    name VARCHAR(255) NOT NULL,
    topic TEXT,
    category VARCHAR(255),
    position INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Users table
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    discriminator VARCHAR(10),
    display_name VARCHAR(255),
    avatar_url TEXT,
    bot BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Messages table
CREATE TABLE IF NOT EXISTS messages (
    message_id BIGINT PRIMARY KEY,
    channel_id BIGINT NOT NULL REFERENCES channels(channel_id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    content TEXT,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    edited_timestamp TIMESTAMP WITH TIME ZONE,
    deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    message_type VARCHAR(50) DEFAULT 'default',
    
    -- Message metadata
    mentions BIGINT[],
    mention_roles BIGINT[],
    attachments JSONB,
    embeds JSONB,
    reactions JSONB,
    
    -- Thread metadata
    thread_id BIGINT,
    
    -- References (replies, pins, etc.)
    reference_message_id BIGINT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Backfill tracking table
CREATE TABLE IF NOT EXISTS backfill_jobs (
    id SERIAL PRIMARY KEY,
    channel_id BIGINT NOT NULL REFERENCES channels(channel_id) ON DELETE CASCADE,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- pending, running, completed, failed
    messages_imported INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance

-- Messages indexes
CREATE INDEX IF NOT EXISTS idx_messages_channel_timestamp 
    ON messages(channel_id, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_messages_user 
    ON messages(user_id);

CREATE INDEX IF NOT EXISTS idx_messages_timestamp 
    ON messages(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_messages_deleted 
    ON messages(deleted) WHERE deleted = FALSE;

CREATE INDEX IF NOT EXISTS idx_messages_thread 
    ON messages(thread_id) WHERE thread_id IS NOT NULL;

-- Full-text search index on message content
CREATE INDEX IF NOT EXISTS idx_messages_content_fts 
    ON messages USING gin(to_tsvector('english', content));

-- Channels indexes
CREATE INDEX IF NOT EXISTS idx_channels_server 
    ON channels(server_id);

CREATE INDEX IF NOT EXISTS idx_channels_subnet 
    ON channels(subnet_id);

-- Subnet name index
CREATE INDEX IF NOT EXISTS idx_subnets_name 
    ON subnets(name);

-- Backfill jobs index
CREATE INDEX IF NOT EXISTS idx_backfill_channel_status 
    ON backfill_jobs(channel_id, status);

-- Create a view for easy subnet message querying
CREATE OR REPLACE VIEW subnet_messages AS
SELECT 
    s.name AS subnet_name,
    s.description AS subnet_description,
    c.channel_id,
    c.name AS channel_name,
    m.message_id,
    m.content,
    m.timestamp,
    m.edited_timestamp,
    m.deleted,
    u.user_id,
    u.username,
    u.display_name,
    u.bot,
    m.attachments,
    m.embeds,
    m.reactions
FROM messages m
JOIN channels c ON m.channel_id = c.channel_id
JOIN users u ON m.user_id = u.user_id
LEFT JOIN subnets s ON c.subnet_id = s.id
WHERE m.deleted = FALSE
ORDER BY m.timestamp DESC;

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_servers_updated_at BEFORE UPDATE ON servers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_channels_updated_at BEFORE UPDATE ON channels
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_messages_updated_at BEFORE UPDATE ON messages
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_subnets_updated_at BEFORE UPDATE ON subnets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_backfill_jobs_updated_at BEFORE UPDATE ON backfill_jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

