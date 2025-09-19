"""Database models and schema for agent system."""

# Database schema for Supabase
DATABASE_SCHEMA = """
-- Agent Chat Sessions
CREATE TABLE IF NOT EXISTS agent_chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    agent_type TEXT NOT NULL CHECK (agent_type IN ('super_admin', 'course_instructor')),
    agent_id UUID NULL, -- References course_assistants.id for course agents
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Agent Messages
CREATE TABLE IF NOT EXISTS agent_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES agent_chat_sessions(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Course Assistants
CREATE TABLE IF NOT EXISTS course_assistants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_by UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    subject TEXT NOT NULL,
    description TEXT,
    role_instructions TEXT NOT NULL,
    constraints TEXT,
    system_prompt TEXT NOT NULL,
    temperature REAL DEFAULT 0.7 CHECK (temperature >= 0.0 AND temperature <= 2.0),
    max_tokens INTEGER CHECK (max_tokens > 0),
    is_active BOOLEAN DEFAULT TRUE,
    openai_assistant_id TEXT UNIQUE,
    vector_store_id TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Agent Files
CREATE TABLE IF NOT EXISTS agent_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    uploaded_by UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    original_filename TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_size INTEGER NOT NULL CHECK (file_size > 0),
    upload_path TEXT NOT NULL,
    openai_file_id TEXT,
    processing_status TEXT DEFAULT 'pending' CHECK (processing_status IN ('pending', 'processing', 'processed', 'failed')),
    error_message TEXT,
    assistant_id UUID REFERENCES course_assistants(id) ON DELETE SET NULL,
    vector_store_id TEXT,
    chunk_count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_agent_chat_sessions_user_id ON agent_chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_agent_chat_sessions_agent_type ON agent_chat_sessions(agent_type);
CREATE INDEX IF NOT EXISTS idx_agent_chat_sessions_created_at ON agent_chat_sessions(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_agent_messages_session_id ON agent_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_agent_messages_user_id ON agent_messages(user_id);
CREATE INDEX IF NOT EXISTS idx_agent_messages_created_at ON agent_messages(created_at);

CREATE INDEX IF NOT EXISTS idx_course_assistants_created_by ON course_assistants(created_by);
CREATE INDEX IF NOT EXISTS idx_course_assistants_subject ON course_assistants(subject);
CREATE INDEX IF NOT EXISTS idx_course_assistants_is_active ON course_assistants(is_active);

CREATE INDEX IF NOT EXISTS idx_agent_files_uploaded_by ON agent_files(uploaded_by);
CREATE INDEX IF NOT EXISTS idx_agent_files_assistant_id ON agent_files(assistant_id);
CREATE INDEX IF NOT EXISTS idx_agent_files_processing_status ON agent_files(processing_status);
CREATE INDEX IF NOT EXISTS idx_agent_files_created_at ON agent_files(created_at DESC);

-- Enable Row Level Security
ALTER TABLE agent_chat_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE course_assistants ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_files ENABLE ROW LEVEL SECURITY;

-- RLS Policies for agent_chat_sessions
DROP POLICY IF EXISTS "Users can view their own chat sessions" ON agent_chat_sessions;
CREATE POLICY "Users can view their own chat sessions"
ON agent_chat_sessions FOR SELECT
USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can create their own chat sessions" ON agent_chat_sessions;
CREATE POLICY "Users can create their own chat sessions"
ON agent_chat_sessions FOR INSERT
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update their own chat sessions" ON agent_chat_sessions;
CREATE POLICY "Users can update their own chat sessions"
ON agent_chat_sessions FOR UPDATE
USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete their own chat sessions" ON agent_chat_sessions;
CREATE POLICY "Users can delete their own chat sessions"
ON agent_chat_sessions FOR DELETE
USING (auth.uid() = user_id);

-- RLS Policies for agent_messages
DROP POLICY IF EXISTS "Users can view their own messages" ON agent_messages;
CREATE POLICY "Users can view their own messages"
ON agent_messages FOR SELECT
USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can create their own messages" ON agent_messages;
CREATE POLICY "Users can create their own messages"
ON agent_messages FOR INSERT
WITH CHECK (auth.uid() = user_id);

-- RLS Policies for course_assistants
DROP POLICY IF EXISTS "Users can view course assistants they created" ON course_assistants;
CREATE POLICY "Users can view course assistants they created"
ON course_assistants FOR SELECT
USING (auth.uid() = created_by);

DROP POLICY IF EXISTS "Super admins can create course assistants" ON course_assistants;
CREATE POLICY "Super admins can create course assistants"
ON course_assistants FOR INSERT
WITH CHECK (
    auth.uid() = created_by AND
    (
        EXISTS (SELECT 1 FROM user_roles WHERE user_id = auth.uid() AND role = 'super_admin') OR
        EXISTS (SELECT 1 FROM organization_memberships WHERE user_id = auth.uid() AND role = 'organization_admin')
    )
);

DROP POLICY IF EXISTS "Users can update course assistants they created" ON course_assistants;
CREATE POLICY "Users can update course assistants they created"
ON course_assistants FOR UPDATE
USING (auth.uid() = created_by);

DROP POLICY IF EXISTS "Users can delete course assistants they created" ON course_assistants;
CREATE POLICY "Users can delete course assistants they created"
ON course_assistants FOR DELETE
USING (auth.uid() = created_by);

-- RLS Policies for agent_files
DROP POLICY IF EXISTS "Users can view their own files" ON agent_files;
CREATE POLICY "Users can view their own files"
ON agent_files FOR SELECT
USING (auth.uid() = uploaded_by);

DROP POLICY IF EXISTS "Users can upload files" ON agent_files;
CREATE POLICY "Users can upload files"
ON agent_files FOR INSERT
WITH CHECK (auth.uid() = uploaded_by);

DROP POLICY IF EXISTS "Users can update their own files" ON agent_files;
CREATE POLICY "Users can update their own files"
ON agent_files FOR UPDATE
USING (auth.uid() = uploaded_by);

DROP POLICY IF EXISTS "Users can delete their own files" ON agent_files;
CREATE POLICY "Users can delete their own files"
ON agent_files FOR DELETE
USING (auth.uid() = uploaded_by);

-- Functions for automatic timestamping
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add triggers for updated_at
DROP TRIGGER IF EXISTS update_agent_chat_sessions_updated_at ON agent_chat_sessions;
CREATE TRIGGER update_agent_chat_sessions_updated_at
    BEFORE UPDATE ON agent_chat_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_course_assistants_updated_at ON course_assistants;
CREATE TRIGGER update_course_assistants_updated_at
    BEFORE UPDATE ON course_assistants
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_agent_files_updated_at ON agent_files;
CREATE TRIGGER update_agent_files_updated_at
    BEFORE UPDATE ON agent_files
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Views for easier querying
CREATE OR REPLACE VIEW agent_session_stats AS
SELECT 
    s.id,
    s.user_id,
    s.title,
    s.agent_type,
    s.agent_id,
    s.created_at,
    COUNT(m.id) as message_count,
    MAX(m.created_at) as last_message_at
FROM agent_chat_sessions s
LEFT JOIN agent_messages m ON s.id = m.session_id
GROUP BY s.id, s.user_id, s.title, s.agent_type, s.agent_id, s.created_at;

CREATE OR REPLACE VIEW course_assistant_stats AS
SELECT 
    ca.id,
    ca.name,
    ca.subject,
    ca.created_by,
    ca.is_active,
    ca.created_at,
    COUNT(DISTINCT s.id) as session_count,
    COUNT(DISTINCT f.id) as file_count,
    COALESCE(SUM(f.file_size), 0) as total_file_size
FROM course_assistants ca
LEFT JOIN agent_chat_sessions s ON ca.id = s.agent_id AND s.agent_type = 'course_instructor'
LEFT JOIN agent_files f ON ca.id = f.assistant_id
GROUP BY ca.id, ca.name, ca.subject, ca.created_by, ca.is_active, ca.created_at;
"""
