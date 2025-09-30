from dotenv import load_dotenv
import os

load_dotenv()

class Frontend:
    URL: str = os.getenv("FRONTEND_URL")
    
class App:
    allowed_origins: list[str] = (
        os.getenv("ALLOWED_ORIGINS", "").split(",") if os.getenv("ALLOWED_ORIGINS") else []
    )

class JWT:
    SECRET: str = os.getenv("JWT_SECRET")
    ALGORITHM: str = os.getenv("JWT_ALGORITHM")
    
class Supabase:
    URL: str = os.getenv("SUPABASE_URL")
    SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY")

class Redis:
    URL: str = os.getenv("REDIS_URL")

class OPA:
    URL: str = os.getenv("OPA_URL")

class OpenAI:
    API_KEY: str = os.getenv("OPENAI_API_KEY")
    ORG_ID: str = os.getenv("OPENAI_ORG_ID")  # Optional

class Config:
    app: App = App()
    supabase: Supabase = Supabase()
    jwt: JWT = JWT()
    redis: Redis = Redis()
    opa: OPA = OPA()
    openai: OpenAI = OpenAI()

config = Config()