import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";

export function useSession() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    apiGet("/auth/me")
      .then((d) => {
        if (!mounted) return;
        setData(d);
        // persist token2 if provided
        if (typeof window !== "undefined" && d?.token2) {
          try { localStorage.setItem("token2", d.token2); } catch {}
        }
      })
      .catch((e) => { if (mounted) setError(String(e)); })
      .finally(() => { if (mounted) setLoading(false); });
    return () => { mounted = false; };
  }, []);

  return { session: data, loading, error };
}

