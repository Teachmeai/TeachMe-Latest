-- Chat persistence: threads and messages
-- chat threads
CREATE TABLE IF NOT EXISTS public.chat_threads (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    assistant_id uuid NOT NULL REFERENCES public.assistants(id) ON DELETE CASCADE,
    course_id uuid REFERENCES public.courses(id) ON DELETE CASCADE,
    org_id uuid REFERENCES public.organizations(id) ON DELETE CASCADE,
    role text CHECK (role IN ('super_admin','organization_admin','teacher','student')),
    openai_thread_id text NOT NULL,
    title text,
    last_message_at timestamp DEFAULT now(),
    created_at timestamp DEFAULT now(),
    updated_at timestamp DEFAULT now()
);
CREATE INDEX IF NOT EXISTS chat_threads_user_idx ON public.chat_threads(user_id);
CREATE INDEX IF NOT EXISTS chat_threads_course_idx ON public.chat_threads(course_id);
CREATE INDEX IF NOT EXISTS chat_threads_assistant_idx ON public.chat_threads(assistant_id);
-- chat messages
CREATE TABLE IF NOT EXISTS public.chat_messages (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    thread_id uuid NOT NULL REFERENCES public.chat_threads(id) ON DELETE CASCADE,
    role text NOT NULL CHECK (role IN ('user','assistant','system','tool')),
    content text,
    openai_message_id text,
    tool_call jsonb DEFAULT '{}'::jsonb,
    created_at timestamp DEFAULT now()
);
CREATE INDEX IF NOT EXISTS chat_messages_thread_idx ON public.chat_messages(thread_id);