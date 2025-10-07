## Authentication setup: Email OTP and Google OAuth

Configure Supabase authentication for Email OTP (magic code) and Google OAuth.

### 1) Enable providers in Supabase
Supabase Dashboard → Authentication → Providers
- Enable Email (magic link/OTP)
- Enable Google and enter your credentials

### 2) Email OTP template (Magic Code)
Set the Email OTP template as HTML in Supabase → Authentication → Templates → Magic link / OTP.

Use this body exactly:

```
<h2>Your verification code</h2>
<p>Enter this 6-digit code to verify your email:</p>
<h1 style="font-size: 2rem; letter-spacing: 0.5rem; color: #3b82f6;">{{ .Token }}</h1>
<p>This code expires in 5 minutes.</p>
<p>If you didn't request this code, please ignore this email.</p>
```

### 3) Google OAuth credentials
Create credentials in Google Cloud Console:
- OAuth 2.0 Client ID (Web application)
- Authorized JavaScript origins: your frontend URL (e.g., http://localhost:3000)
- Authorized redirect URIs: `http://localhost:3000/auth/callback`

Populate your backend `.env` names:
```
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=
FRONTEND_URL=
```

Populate your frontend `ascend-educate-nextjs/.env.local` names:
```
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
```

### 4) JWT secret for backend validation
In Supabase Dashboard → Settings → API → JWT, copy the JWT secret. Put it in your backend `.env`:
```
JWT_SECRET=
JWT_ALGORITHM=HS256
```

The backend validates Supabase-issued access tokens using these values.


