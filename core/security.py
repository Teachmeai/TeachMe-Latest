from fastapi.security import HTTPBearer

# global security scheme instance
security = HTTPBearer(
    scheme_name="Bearer",
    description="JWT Bearer token for authentication"
)