import { useCallback, useEffect, useRef, useState } from "react";
import { apiGet, apiPost, getAuthHeaders } from "@/lib/api";

export function useChat(threadId?: string) {
  const [messages, setMessages] = useState<any[]>([]);
  const [sending, setSending] = useState(false);
  const evtSrcRef = useRef<EventSource | null>(null);

  const load = useCallback(async () => {
    if (!threadId) return;
    const data = await apiGet(`/assistant/chats/${threadId}/messages?page=1&page_size=50`);
    setMessages(data.messages || []);
  }, [threadId]);

  const send = useCallback(async (text: string, stream = false) => {
    if (!threadId || !text) return;
    const optimistic = { id: `tmp-${Date.now()}`, role: "user", content: text, created_at: new Date().toISOString() };
    setMessages((prev) => [...prev, optimistic]);
    setSending(true);
    try {
      if (stream) {
        // SSE call
        const headers = getAuthHeaders();
        const token = (headers["Authorization"] || "").replace("Bearer ", "");
        const qs = new URLSearchParams({});
        const url = `/assistant/chats/send/stream`;
        const es = new EventSource(url, { withCredentials: false } as any);
        evtSrcRef.current = es;
        await apiPost(`/assistant/chats/send`, { thread_id: threadId, message: text });
        // Fallback: load after send completes (basic behavior)
        await load();
      } else {
        const data = await apiPost(`/assistant/chats/send`, { thread_id: threadId, message: text });
        // Add AI response messages to the list
        if (data.messages && data.messages.length > 0) {
          const aiMessages = data.messages.map((m: any, i: number) => ({ 
            id: `${m.openai_message_id || 'ai'}-${i}`, 
            role: "assistant", 
            content: m.content,
            created_at: new Date().toISOString()
          }));
          setMessages((prev) => [...prev, ...aiMessages]);
        }
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      // Remove the optimistic user message on error
      setMessages((prev) => prev.filter(msg => msg.id !== optimistic.id));
    } finally {
      setSending(false);
    }
  }, [threadId, load]);

  useEffect(() => { load(); }, [load]);
  return { messages, load, send, sending };
}

