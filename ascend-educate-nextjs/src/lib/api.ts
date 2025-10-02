function getBaseUrl() {
  // Prefer explicit env, else fall back to localhost:8000
  const env = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (env && env.trim().length > 0) return env.replace(/\/$/, "");
  if (typeof window !== "undefined") {
    // If backend is hosted on same origin under /api, you can change this
    return "http://127.0.0.1:8000";
  }
  return "http://127.0.0.1:8000";
}

export async function getAuthHeaders() {
  if (typeof window === "undefined") return {} as Record<string, string>;
  
  // Import supabase dynamically to avoid SSR issues
  const { supabase } = await import('./supabase');
  const { data: { session } } = await supabase.auth.getSession();
  const token = session?.access_token;
  
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function apiGet<T = any>(path: string): Promise<T> {
  const url = `${getBaseUrl()}${path.startsWith("/") ? path : `/${path}`}`;
  const authHeaders = await getAuthHeaders();
  const res = await fetch(url, { headers: authHeaders });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function apiPost<T = any>(path: string, body?: any): Promise<T> {
  const url = `${getBaseUrl()}${path.startsWith("/") ? path : `/${path}`}`;
  const authHeaders = await getAuthHeaders();
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

