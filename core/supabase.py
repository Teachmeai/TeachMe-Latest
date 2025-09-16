from supabase import create_client, Client
from core.config import config

# global clients
supabase_admin: Client | None = None
supabase_anon: Client | None = None

def init_supabase():
    """
    Initialize both service role (admin) and anon clients (synchronous)
    """
    global supabase_admin, supabase_anon

    supabase_admin = create_client(
        supabase_url=config.supabase.URL,
        supabase_key=config.supabase.SERVICE_ROLE_KEY,
    )

    supabase_anon = create_client(
        supabase_url=config.supabase.URL,
        supabase_key=config.supabase.ANON_KEY,
    )


# dependencies
def get_supabase_admin() -> Client:
    if supabase_admin is None:
        raise RuntimeError("supabase admin client not initialized")
    return supabase_admin


def get_supabase_anon() -> Client:
    if supabase_anon is None:
        raise RuntimeError("supabase anon client not initialized")
    return supabase_anon