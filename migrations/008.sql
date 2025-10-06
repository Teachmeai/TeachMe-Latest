-- Course invites table for inviting students to courses
CREATE TABLE public.course_invites (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id uuid NOT NULL REFERENCES public.courses(id) ON DELETE CASCADE,
    invitee_email text NOT NULL,
    inviter uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'rejected', 'expired')),
    expires_at timestamp without time zone NOT NULL,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now()
);

-- Add indexes for performance
CREATE INDEX course_invites_course_idx ON public.course_invites(course_id);
CREATE INDEX course_invites_email_idx ON public.course_invites(invitee_email);
CREATE INDEX course_invites_status_idx ON public.course_invites(status);
CREATE INDEX course_invites_expires_idx ON public.course_invites(expires_at);

-- Unique constraint to prevent duplicate invites
CREATE UNIQUE INDEX course_invites_unique ON public.course_invites(course_id, invitee_email) 
WHERE status = 'pending';
