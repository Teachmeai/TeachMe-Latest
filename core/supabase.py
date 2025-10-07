from supabase import create_client, Client
from core.config import config

# Global clients
supabase_admin: Client | None = None
supabase_anon: Client | None = None


def init_supabase():
    """
    Initialize both service role (admin) and anon clients (synchronous)
    Ensures all queries are executed in the 'public' schema.
    """
    global supabase_admin, supabase_anon

    # --- Admin Client (Service Role) ---
    supabase_admin = create_client(
        supabase_url=config.supabase.URL,
        supabase_key=config.supabase.SERVICE_ROLE_KEY,
    )
    # Ensure all admin queries use public schema
    try:
        supabase_admin.postgrest.schema("public")
    except Exception:
        pass

    # --- Anon Client (Public Key) ---
    supabase_anon = create_client(
        supabase_url=config.supabase.URL,
        supabase_key=config.supabase.ANON_KEY,
    )
    # Ensure all anon queries use public schema
    try:
        supabase_anon.postgrest.schema("public")
    except Exception:
        pass

    print("✅ Supabase initialized with schema: public")
    return supabase_admin, supabase_anon


# --- Dependencies for FastAPI routes ---
def get_supabase_admin() -> Client:
    """
    Returns the initialized Supabase admin client.
    Raises an error if not initialized.
    """
    if supabase_admin is None:
        raise RuntimeError("Supabase admin client not initialized. Call init_supabase() first.")
    # Re-assert 'public' schema on every access to avoid residual schema changes
    try:
        supabase_admin.postgrest.schema("public")
    except Exception:
        pass
    return supabase_admin


def get_supabase_anon() -> Client:
    """
    Returns the initialized Supabase anon client.
    Raises an error if not initialized.
    """
    if supabase_anon is None:
        raise RuntimeError("Supabase anon client not initialized. Call init_supabase() first.")
    # Re-assert 'public' schema on every access to avoid residual schema changes
    try:
        supabase_anon.postgrest.schema("public")
    except Exception:
        pass
    return supabase_anon
