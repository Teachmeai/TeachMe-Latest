import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";

export function useResolvedAssistant(role?: string, orgId?: string, courseId?: string) {
  const [assistant, setAssistant] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!role && !courseId) return;
    setLoading(true);
    const qs = new URLSearchParams();
    if (role) qs.set("role", role);
    if (orgId) qs.set("org_id", orgId);
    if (courseId) qs.set("course_id", courseId);
    apiGet(`/assistants/resolve?${qs.toString()}`)
      .then((d) => setAssistant(d.assistant || null))
      .finally(() => setLoading(false));
  }, [role, orgId, courseId]);

  return { assistant, loading };
}

export function useAssistantsList(scope?: "global"|"organization"|"course", role?: string, orgId?: string, courseId?: string) {
  const [items, setItems] = useState<any[]>([]);
  useEffect(() => {
    const qs = new URLSearchParams();
    if (scope) qs.set("scope", scope);
    if (role) qs.set("role", role);
    if (orgId) qs.set("org_id", orgId);
    if (courseId) qs.set("course_id", courseId);
    apiGet(`/assistants?${qs.toString()}`).then((d) => setItems(d.assistants || []));
  }, [scope, role, orgId, courseId]);
  return items;
}

