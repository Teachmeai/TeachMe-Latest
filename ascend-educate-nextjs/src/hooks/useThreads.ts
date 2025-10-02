import { useCallback, useEffect, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";

export function useThreads(filter: { assistantId?: string; courseId?: string }) {
  const [threads, setThreads] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [updating, setUpdating] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const load = useCallback(async () => {
    if (!filter.assistantId) return; // Don't load if no assistant context
    setLoading(true);
    try {
      const qs = new URLSearchParams();
      if (filter.courseId) qs.set("course_id", filter.courseId);
      const data = await apiGet(`/assistant/chats?${qs.toString()}`);
      setThreads(data.threads || []);
    } catch (error) {
      console.error("Failed to load threads:", error);
      setThreads([]);
    } finally {
      setLoading(false);
    }
  }, [filter.assistantId, filter.courseId]);

  const create = useCallback(async (title?: string) => {
    if (!filter.assistantId) throw new Error("assistantId required");
    setCreating(true);
    try {
      const body: any = { assistant_id: filter.assistantId };
      if (filter.courseId) body.course_id = filter.courseId;
      if (title) body.title = title;
      const data = await apiPost("/assistant/chats", body);
      setThreads((prev) => [data.thread, ...prev]);
      return data.thread;
    } finally {
      setCreating(false);
    }
  }, [filter.assistantId, filter.courseId]);

  const rename = useCallback(async (threadId: string, title: string) => {
    setUpdating(true);
    try {
      // Try direct POST rename endpoint (backend exposes it)
      await apiPost(`/assistant/chats/${threadId}/rename`, { title } as any);
      setThreads((prev) => prev.map((t) => (t.id === threadId ? { ...t, title } : t)));
    } finally {
      setUpdating(false);
    }
  }, []);

  const remove = useCallback(async (threadId: string) => {
    setDeleting(true);
    try {
      // Try direct POST delete endpoint (backend exposes it)
      await apiPost(`/assistant/chats/${threadId}/delete`, {} as any);
      setThreads((prev) => prev.filter((t) => t.id !== threadId));
    } finally {
      setDeleting(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);
  return { threads, loading, creating, updating, deleting, reload: load, create, rename, remove };
}

