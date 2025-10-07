## TeachMe Frontend (Next.js)

Next.js app for TeachMe. Auth via Supabase; talks to the FastAPI backend using environment-configured URLs.

## Environment Variables (.env.local)
Create `ascend-educate-nextjs/.env.local` with:

```
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
NEXT_PUBLIC_BACKEND_URL=
```

Notes:
- The app reads `NEXT_PUBLIC_BACKEND_URL` to avoid hardcoding the API URL [[memory:4484824]].
- If omitted, some utilities fall back to `http://127.0.0.1:8000`.

## Install and Run
```bash
cd ascend-educate-nextjs
npm install
npm run dev
```

Open `http://localhost:3000`.

## Backend Requirements
Ensure the backend is running at the URL specified by `NEXT_PUBLIC_BACKEND_URL`. See project root `README.md` for backend setup.

## Deploy
For deployment, configure `NEXT_PUBLIC_*` variables in your hosting provider. If using Render, set `NEXT_PUBLIC_BACKEND_URL` according to your backend service URL; the app already expects this env at runtime.
