# Deployment runbook (M5)

Deploy the backend to **Render** and the frontend to **Vercel**, both from a
GitHub repo. Follow the steps in order. The order matters because the frontend
needs the backend URL at build time, and the backend needs the frontend URL for
CORS.

Time estimate: about 30-45 minutes the first time.

---

## 0. Prerequisites

- Accounts: GitHub, Render (render.com), Vercel (vercel.com). Free tiers are fine.
- Your Supabase project (you can reuse the same one you used in development).
- Both migrations already applied in Supabase:
  `supabase/migrations/0001_init.sql` and `0002_response_limit.sql`.
- The Supabase values you used locally (Project Settings > API):
  - Project URL
  - `anon` / publishable key (frontend)
  - `service_role` / secret key (backend only)
  - JWT Secret (backend only)

Note on secrets: `backend/.env` and `frontend/.env.local` are git-ignored and are
NOT in this bundle. You will re-enter these values in the Render and Vercel
dashboards, not in files.

---

## 1. Push the code to GitHub

From the project folder:

```bash
# one-time identity if not set globally
git config user.email "you@example.com"
git config user.name "Your Name"

git init                 # only if .git does not already exist
git add -A
git commit -m "Mingle MVP"
git branch -M main

# create an EMPTY repo on github.com first (no README), then:
git remote add origin https://github.com/<you>/mingle.git
git push -u origin main
```

Sanity check that no secrets were committed (should print nothing):

```bash
git ls-files | grep -E "\.env$|\.env\.local$"
```

---

## 2. Deploy the backend to Render (do this first)

You have a `render.yaml` blueprint and a `backend/Dockerfile`.

### Option A - Blueprint (recommended)

1. Render dashboard > New > Blueprint.
2. Connect your GitHub repo. Render reads `render.yaml` and proposes a web
   service named `mingle-api` (Docker, free plan, health check `/api/health`).
3. When prompted, set the secret env vars (they are marked `sync:false`):
   - `SUPABASE_URL` = your project URL
   - `SUPABASE_SERVICE_KEY` = service_role / secret key
   - `SUPABASE_JWT_SECRET` = JWT Secret
   - `CORS_ORIGINS` = leave as a placeholder for now, for example
     `http://localhost:5173` (you will update it in step 4)
   - `FRONTEND_BASE_URL` = placeholder for now (update in step 4)
   - `ENVIRONMENT` = `prod` and `RESPONSE_HARD_CAP` = `200` come from the blueprint
4. Create and let it build. First build pulls the uv image and installs deps.
5. Copy the service URL, for example `https://mingle-api.onrender.com`.
6. Verify: open `https://mingle-api.onrender.com/api/health`. You want
   `{"status":"ok", ... , "supabase_configured": true}`.

### Option B - Manual (if you skip the blueprint)

New > Web Service > connect repo > Root Directory `backend` > it detects the
Dockerfile > add the same env vars as above > set health check path
`/api/health` > Create.

Note: on the free plan the service sleeps after inactivity, so the first request
after idle can take ~50 seconds. That is expected.

---

## 3. Deploy the frontend to Vercel

1. Vercel dashboard > Add New > Project > import your GitHub repo.
2. Set **Root Directory** to `frontend`. Vercel detects Vite (there is also a
   `frontend/vercel.json` that sets the build and the SPA rewrite).
3. Add Environment Variables (Production):
   - `VITE_SUPABASE_URL` = your project URL
   - `VITE_SUPABASE_ANON_KEY` = anon / publishable key
   - `VITE_API_BASE_URL` = `https://mingle-api.onrender.com/api` (the Render URL
     from step 2, with `/api`)
4. Deploy. Copy the resulting URL, for example `https://mingle.vercel.app`.

The `vercel.json` rewrite is important: it serves `index.html` for all routes so
deep links like `/r/<token>` and `/result/<token>` work on direct open or refresh.

---

## 4. Wire the two together

Now that you know both URLs, close the loop.

1. **Render** > `mingle-api` > Environment: set
   - `CORS_ORIGINS` = `https://mingle.vercel.app` (add `,http://localhost:5173`
     too if you still want local dev to hit prod)
   - `FRONTEND_BASE_URL` = `https://mingle.vercel.app`
   Save. Render redeploys automatically.

2. **Supabase** > Authentication > URL Configuration:
   - Site URL = `https://mingle.vercel.app`
   - Redirect URLs: add `https://mingle.vercel.app/**`
   (Keep `http://localhost:5173/**` as well if you want local login to keep working.)

3. **Google Cloud Console** (only if login fails): your OAuth client's Authorized
   redirect URI should already be the Supabase callback
   `https://<project>.supabase.co/auth/v1/callback`. No app-domain change is
   normally needed, because Google redirects to Supabase, which then redirects to
   your app.

---

## 5. Verify end to end

On the live Vercel URL:

1. Landing page loads and explains the app.
2. Create a catch-up: sign in with Google, add 2-3 time options, create, get a
   link.
3. Open the invite link in an incognito window (no account): submit a response.
4. Open the result link: you see the best time, group size, budget band, and
   suggestions. Confirm no individual budgets are shown.

If sign-in bounces back or you get a redirect error, re-check step 4.2 (Supabase
redirect URLs must include your Vercel domain).

If the first API call is slow, that is the Render free-tier cold start.

---

## 6. Custom domain (after you buy one)

1. **Vercel** > Project > Settings > Domains: add your domain and follow the DNS
   instructions (add the CNAME/A records at your registrar).
2. Update **Render** `CORS_ORIGINS` and `FRONTEND_BASE_URL` to the new domain.
3. Update **Supabase** Auth Site URL and Redirect URLs to the new domain.
4. Redeploy the backend so it picks up the new env values.

Optional: put the backend on a subdomain like `api.yourdomain.com` (Render >
Settings > Custom Domains) and update `VITE_API_BASE_URL` in Vercel accordingly.

---

## Troubleshooting

- **CORS error in the browser**: `CORS_ORIGINS` on Render must exactly match the
  frontend origin (scheme + host, no trailing slash). Redeploy after changing.
- **401 on create**: JWT verification issue. Confirm `SUPABASE_JWT_SECRET` and
  `SUPABASE_URL` are set on Render; the backend verifies via JWKS with an HS256
  fallback.
- **Login redirect mismatch**: add your exact deployed URL to Supabase Auth
  Redirect URLs.
- **`supabase_configured: false` at /api/health**: `SUPABASE_URL` or
  `SUPABASE_SERVICE_KEY` is missing on Render.
- **Deep link 404 on Vercel**: ensure `frontend/vercel.json` is present (SPA
  rewrite).
