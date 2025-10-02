-- Phase 5: archival support on chat_threads

ALTER TABLE public.chat_threads
ADD COLUMN IF NOT EXISTS archived_at timestamp NULL;

CREATE INDEX IF NOT EXISTS chat_threads_archived_idx ON public.chat_threads(archived_at);


