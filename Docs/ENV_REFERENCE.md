## Environment variables reference

Centralized list of environment variable names used by this project. Fill values in your local `.env` and `.env.local` files.

### Backend (.env)
```
# Supabase
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
SUPABASE_ANON_KEY=

# Auth/JWT
JWT_SECRET=
JWT_ALGORITHM=HS256

# App URLs / CORS
FRONTEND_URL=
ALLOWED_ORIGINS=

# Redis / OPA
REDIS_URL=
OPA_URL=

# Email (SMTP)
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_FROM=
MAIL_PORT=587
MAIL_SERVER=smtp.gmail.com

# OpenAI
OPENAI_API_KEY=
OPENAI_ORG_ID=
```

### Frontend (ascend-educate-nextjs/.env.local)
```
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=

# Backend base URL used by the frontend
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

Notes:
- The frontend reads `NEXT_PUBLIC_BACKEND_URL` at runtime, so avoid hardcoding the API URL in code.
- If deploying, set these variables in your hosting provider's dashboard.


