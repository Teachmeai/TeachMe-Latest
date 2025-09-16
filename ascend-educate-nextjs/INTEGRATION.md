# Backend Integration Setup

Your Next.js frontend is now integrated with the Teachme backend. Here's what was added and how to use it.

## What's Integrated

### 1. Supabase Authentication
- **Magic Link Login**: Users can sign in via email magic link
- **Google OAuth**: Users can sign in with Google
- **Auto Session Management**: Handles auth state changes automatically

### 2. Backend API Integration
- **Session Management**: Fetches user roles and active role from backend
- **Role Switching**: Users can switch between available roles (global + org-scoped)
- **Device Tracking**: Each session includes a unique device ID

### 3. Role System
- **Global Roles**: `super_admin`, `teacher`, `student` (stored in `user_roles`)
- **Org Roles**: `organization_admin`, `teacher`, `student` (stored in `organization_memberships`)
- **Multi-role Support**: Users can have multiple roles across different organizations

## Setup Instructions

### 1. Install Dependencies
```bash
cd ascend-educate-nextjs
npm install
```

### 2. Environment Variables
Copy `env.local` to `.env.local`:
```bash
cp env.local .env.local
```

Your `.env.local` should contain:
```env
NEXT_PUBLIC_SUPABASE_URL=https://zwbdjtoqlxtcgngldvti.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

### 3. Start Development
```bash
npm run dev
```

### 4. Ensure Backend is Running
Make sure your FastAPI backend is running on http://localhost:8000 with:
- Redis running (localhost:6379)
- OPA running (localhost:8181)
- Supabase database with the new schema applied

## How It Works

### Authentication Flow
1. User signs in via magic link or Google OAuth
2. Supabase creates/updates user in `auth.users`
3. Database triggers create profile and default `student` role
4. Frontend calls `/auth/me` to get session with roles
5. User can switch roles via `/auth/switch-role`

### Role Management
- **Default Role**: New users get `student` role automatically
- **Role Switching**: Users can switch between their available roles
- **Session Persistence**: Active role is stored in Redis and `profiles.active_role`
- **Multi-org Support**: Users can be teacher in Org A, student in Org B, etc.

### Components Added
- `useAuth()` hook: Manages authentication state and backend session
- `RoleSwitcher` component: Dropdown to switch between available roles
- `BackendClient`: Handles all API calls to your FastAPI backend

## Testing the Integration

1. **Sign Up**: Create a new account via magic link or Google
2. **Check Roles**: Verify you get a default `student` role
3. **Role Switching**: If you have multiple roles, test switching
4. **Session Persistence**: Refresh page and verify role is maintained
5. **Logout**: Test that logout clears both Supabase and backend sessions

## Next Steps

To complete the integration, you may want to:

1. **Add Role-based UI**: Show/hide features based on user roles
2. **Organization Management**: Add UI for creating/managing organizations
3. **Invite System**: Add UI for sending/accepting invites
4. **Profile Completion**: Connect profile forms to backend user data
5. **Chat Integration**: Connect chat features to backend APIs

## Troubleshooting

- **CORS Issues**: Ensure backend CORS allows `http://localhost:3000`
- **JWT Errors**: Verify `JWT_SECRET` matches between frontend and backend
- **Role Not Found**: Check that user has roles in `user_roles` or `organization_memberships`
- **Session Not Loading**: Verify Redis is running and accessible

## API Endpoints Used

- `GET /auth/me` - Get user session and roles
- `POST /auth/switch-role` - Switch active role
- `POST /auth/logout` - Clear session

All requests include `Authorization: Bearer <jwt>` header and optional `X-Device-Id` header.
