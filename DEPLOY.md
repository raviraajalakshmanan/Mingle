# DEPLOY.md - deployment rules and replay guide

Written after the first successful production deploy of MigleUp on 2026-08-20.

`DEPLOYMENT.md` is the original short runbook. **This file is the one to read
first.** It records what actually happened, the traps that cost time, and a
checklist you can reuse for any Vite + FastAPI + Supabase app on Vercel + Render.

---

## 1. What is deployed right now

| Piece | Where | URL |
|---|---|---|
| Backend (FastAPI, Docker) | Render, free plan | `https://mingle-api-bpnf.onrender.com` |
| Frontend (React + Vite) | Vercel | `https://mingle-ochre.vercel.app` |
| Database + Auth | Supabase | project URL in env vars, never in git |

Health probe: `curl -s https://mingle-api-bpnf.onrender.com/api/health`

Expected: `{"status":"ok","service":"MigleUp","version":"0.1.0","environment":"prod","supabase_configured":true}`

Render service name is `mingle-api`. Render appended the random suffix `-bpnf`,
so never hardcode the service name into a URL. Always copy the real one from the
dashboard.

> **Naming note.** The product was renamed to MigleUp, but every hosting slug
> above still says `mingle`. That is intentional, not a stale doc: these are the
> live resource names, and the URLs only resolve under them. Renaming a Render
> service or a Vercel project issues a new URL, so it has to be done in the
> dashboards together with `CORS_ORIGINS`, `FRONTEND_BASE_URL`,
> `VITE_API_BASE_URL`, and the Supabase Site URL and redirect URLs. Until then,
> the `service` field in the health response reads `MigleUp` while the host still
> reads `mingle-api`, which is expected.

---

## 2. The golden rules

These are the things that actually break deploys. Read them before touching
anything.

### R1. Order matters: backend, then frontend, then wiring

The frontend needs the API URL **at build time**, and the backend needs the
frontend origin for CORS. So there is no order that avoids a placeholder. The
resolution is: deploy the backend first with placeholder CORS values, deploy the
frontend with the real API URL, then go back and correct the backend. Three
steps, one loop closed at the end.

### R2. Vite bakes env vars into the bundle at build time

`VITE_*` variables are substituted into the JavaScript when the build runs. They
are not read at runtime. Two consequences:

1. Changing a variable in the Vercel dashboard does **nothing** to the live site.
   You must trigger a rebuild: Deployments, top deployment, "..." menu, Redeploy.
2. Every variable must be correct **before** the first build, or you ship a
   broken bundle that looks fine until someone clicks something.

### R3. A missing frontend env var fails silently, not loudly

In `src/lib/api.ts`:

```ts
const API_BASE = (import.meta.env.VITE_API_BASE_URL as string) ?? "http://localhost:8000/api";
```

If the variable is absent, the fallback bakes `http://localhost:8000/api` into
production and the live site tries to call the visitor's own machine. If the
variable is present but **empty**, `??` does not catch an empty string, so calls
go to the Vercel domain itself and 404.

Same shape in `src/lib/supabase.ts`: missing keys make the client `null`, and
sign-in throws "Supabase is not configured" instead of naming the missing var.

**Rule: after the first deploy, open DevTools, Network tab, reload, and confirm
requests point at the real API host.** That single check catches all of these.

### R4. CORS origins are exact string matches, no trailing slash

`main.py` uses `allow_credentials=True` with an explicit origin list. That means:

- No wildcard. `*` is invalid when credentials are allowed.
- The browser `Origin` header never has a trailing slash, so
  `https://app.vercel.app/` in the list matches nothing. Use
  `https://app.vercel.app`.
- Scheme must match. `http://` will not match an `https://` origin.
- Vercel **preview** deploys get unique per-branch URLs that are not in the list,
  so previews cannot reach the API unless you add them explicitly. For an MVP,
  accept this.

Contrast with `FRONTEND_BASE_URL`, which `catchups.py` passes through
`.rstrip("/")`, so a trailing slash there is harmless. Two variables, two
different levels of tolerance. Do not assume.

### R5. CORS is not a security boundary

CORS is enforced by the browser. It never protected the API. The real guards are
Supabase JWT verification on creator endpoints and unguessable tokens on the
invite and result paths. So keeping `http://localhost:5173` in the production
allow list for debugging costs nothing.

### R6. Env var names fail quietly when misspelled

Pydantic settings falls back to the default when a variable name does not match,
with no warning. `CORS_ORIGINS` is plural. `RESPONSE_HARD_CAP` is not
`RESPONSE_CAP`. Check spelling against `backend/app/core/config.py`, which is the
authoritative list.

### R7. Never commit secrets, and verify it rather than trusting it

`.gitignore` covers `.env` and `.env.local`, but confirm before the first push:

```bash
git ls-files | grep -E "\.env$|\.env\.local$"    # must print nothing
```

A secret inside a git commit stays in history even after you delete the file.
Secrets go in the Render and Vercel dashboards, never in the repo.

Which key goes where matters:
- `service_role` key and JWT secret: **backend only** (Render).
- `anon` key: frontend, safe to ship to the browser, protected by RLS.

Mixing these up leaks full database access into a public JavaScript bundle.

### R8. Free tier Render sleeps

The container spins down after inactivity, so the first request after idle takes
roughly 50 seconds. This is cold start, not a bug. Do not debug it. Warn testers
about it before they conclude the app is broken.

---

## 3. Full replay, step by step

### Step 0. Verify locally before deploying anything

Never deploy code you have not run. All four must pass:

```bash
cd backend && uv sync && uv run ruff check . && uv run pytest -q
cd ../frontend && npm install && npm run lint && npm run build
```

Then start both and confirm they actually serve:

```bash
# terminal 1
cd backend && uv run uvicorn app.main:app --reload
# terminal 2
cd frontend && npm run dev

curl -s http://localhost:8000/api/health     # supabase_configured must be true
curl -s -o /dev/null -w "%{http_code}" http://localhost:5173/   # 200
```

`supabase_configured: false` locally means `backend/.env` is missing or empty.
Fix that before deploying, or you will debug the same problem twice.

### Step 1. Push to GitHub

Create an **empty** repo on github.com first. No README, no .gitignore, no
license. An empty repo avoids a first-push merge conflict.

```bash
cd <project>
git config --global user.email "you@example.com"
git config --global user.name "Your Name"

git init
git add -A
git status          # review before committing
```

Review that list. You want source directories. You do **not** want `.env`,
`.env.local`, `node_modules/`, `dist/`, `.venv/`.

```bash
git commit -m "Initial commit"
git branch -M main
git ls-files | grep -E "\.env$|\.env\.local$"   # must print nothing
git remote add origin https://github.com/<you>/<repo>.git
git push -u origin main
```

If the push asks for a password, GitHub no longer accepts account passwords over
HTTPS. Use a personal access token with `repo` scope, or run `gh auth login`.

### Step 2. Backend to Render

Render dashboard, **New +**, **Blueprint**, connect the repo. Render reads
`render.yaml` and proposes the service.

If the repo is not listed, click Configure GitHub App and grant access.

Fill the vars marked `sync: false` in `render.yaml`:

| Key | Value |
|---|---|
| `SUPABASE_URL` | project URL, no trailing slash |
| `SUPABASE_SERVICE_KEY` | service_role key, backend only |
| `SUPABASE_JWT_SECRET` | JWT secret |
| `CORS_ORIGINS` | `http://localhost:5173` placeholder, corrected in Step 4 |
| `FRONTEND_BASE_URL` | `http://localhost:5173` placeholder, corrected in Step 4 |

`ENVIRONMENT=prod` and `RESPONSE_HARD_CAP=200` come from the blueprint and are
not prompted for.

Click Apply. First build takes 3 to 6 minutes because it pulls the base images
and runs `uv sync --frozen`. Wait for the badge to read **Live**, then verify:

```bash
curl -s https://<service>.onrender.com/api/health
```

`environment` must read `prod` and `supabase_configured` must be `true`.

**On placeholders being safe:** the invite and result URLs are built per request
from `FRONTEND_BASE_URL` and are never stored in the database. Only the tokens
are persisted. So a wrong base URL corrupts nothing and self corrects the moment
you fix the variable. The one caveat is not to create a catch-up you intend to
share during the placeholder window, because the link handed back will point at
localhost. If that happens, the token is still valid, so swap the host by hand.

### Step 3. Frontend to Vercel

vercel.com/new, import the repo.

**Set Root Directory to `frontend`.** This is mandatory. The repo root has no
`package.json`, so the build fails instantly without it. Framework preset flips
to Vite once the root directory is set. Build command and output directory come
from `frontend/vercel.json`.

Environment variables, scoped to Production and Preview:

| Key | Value |
|---|---|
| `VITE_SUPABASE_URL` | project URL |
| `VITE_SUPABASE_ANON_KEY` | anon key, not the service key |
| `VITE_API_BASE_URL` | `https://<service>.onrender.com/api` |

Note the `/api` suffix and no trailing slash after it. `api.ts` concatenates
`${API_BASE}${path}` where path already starts with `/`, so a trailing slash
gives `/api//catchups` and 404s everything.

Deploy, then copy the production URL.

At this point sign-in and API calls still fail. That is expected, because CORS
and the Supabase redirect URLs are not wired yet. What you can check now:

- Landing page renders with correct styling.
- DevTools Network shows requests aimed at the Render host, not localhost.
- A direct visit to a deep route such as `/result/anything` loads the app shell
  rather than a Vercel 404, confirming the SPA rewrite in `vercel.json`.

### Step 4. Close the loop

**Render**, service, Environment, correct both placeholders:

| Key | Value |
|---|---|
| `CORS_ORIGINS` | `https://<app>.vercel.app,http://localhost:5173` |
| `FRONTEND_BASE_URL` | `https://<app>.vercel.app` |

Save. Render redeploys automatically, 2 to 4 minutes. **Wait for Live before
testing**, or you are testing the old container.

**Supabase**, Authentication, URL Configuration:

- Site URL: `https://<app>.vercel.app`
- Redirect URLs: add `https://<app>.vercel.app/**`, keep
  `http://localhost:5173/**` for local login.

The `/**` wildcard matters. `src/lib/auth.tsx` requests
`redirectTo: ${window.location.origin}/new`, so the exact `/new` callback has to
be covered.

These take effect immediately. No redeploy on either side.

**Google Cloud Console**: normally nothing to do. Google redirects to Supabase,
Supabase redirects to the app, so the authorized redirect URI stays
`https://<project>.supabase.co/auth/v1/callback`. Only revisit if the failure
message names Google rather than Supabase.

### Step 5. Verify end to end on the live URL

1. Landing page loads.
2. Sign in with Google, land back on `/new` signed in.
3. Create a catch-up. Confirm the share link uses the real domain, not localhost.
4. Open the invite link in a private window, not signed in, and submit a response.
5. Repeat from a second browser so there is a real overlap to compute.
6. Open the result link. Best time, group size, budget band, suggestions.
7. **Confirm privacy invariant I1 in production**: aggregates only. No name is
   ever paired with a budget or a set of slots.
8. Refresh the result page directly. No 404, which reconfirms the SPA rewrite.

---

## 4. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| CORS error in console | `CORS_ORIGINS` has a typo, a trailing slash, or wrong scheme. Or Render had not finished redeploying. | Correct it, wait for Live. |
| Live site calls `localhost:8000` | `VITE_API_BASE_URL` missing at build time, silent fallback in `api.ts`. | Set it, then **redeploy**. |
| Every API call 404s | `VITE_API_BASE_URL` blank, or trailing slash after `/api`. | Set the exact value, redeploy. |
| "Supabase is not configured" | `VITE_SUPABASE_URL` or anon key missing at build time. | Set both, redeploy. |
| Sign-in bounces or redirect error | Vercel domain not in Supabase Redirect URLs, or missing `/**`. | Add `https://<app>.vercel.app/**`. |
| 401 on create | JWT verification. `SUPABASE_JWT_SECRET` does not match the project. | Recopy from Supabase, save on Render. |
| `supabase_configured: false` | `SUPABASE_URL` or `SUPABASE_SERVICE_KEY` missing on Render. | Set them, redeploy. |
| Deep link 404 on Vercel | `frontend/vercel.json` missing or Root Directory wrong. | Confirm both. |
| Build: lockfile needs update | `uv sync --frozen` refuses a stale `uv.lock`. | Regenerate locally, commit. |
| Build: cannot find `pyproject.toml` | `dockerContext` wrong, or `render.yaml` not at repo root. | Check `render.yaml`. |
| First request takes ~50s | Render free tier cold start. | Expected. Not a bug. |
| Vercel build: no package.json | Root Directory not set to `frontend`. | Set it, redeploy. |

---

## 5. Pre-flight checklist for a new app

Copy this. It generalizes past MigleUp.

**Before pushing**
- [ ] All local checks pass, both lint and tests, both halves of the stack.
- [ ] Both servers start and serve a real response, not just compile.
- [ ] Health endpoint reports its dependencies as configured.
- [ ] `.gitignore` covers `.env`, `.env.local`, `node_modules/`, `dist/`, `.venv/`.
- [ ] `git status` reviewed file by file before the first commit.
- [ ] `git ls-files | grep -E "\.env$|\.env\.local$"` prints nothing.
- [ ] Empty GitHub repo created, no README or license.

**Env var inventory** (write this table out before touching a dashboard)
- [ ] Every backend var, with which are secret.
- [ ] Every frontend var, confirming none is a secret.
- [ ] Which vars are placeholders in round one and get corrected in round two.
- [ ] Every var name checked against the config file that reads it.

**Backend**
- [ ] Container binds the injected `$PORT`, with a local default.
- [ ] Health check path set, and it does not require auth.
- [ ] Deploy reached Live, health verified by curl, environment reads `prod`.

**Frontend**
- [ ] Root directory set if the app is not at the repo root.
- [ ] All build-time vars set **before** the first build.
- [ ] SPA rewrite present if the router uses deep links.
- [ ] DevTools Network confirms calls go to the real API host.

**Wiring**
- [ ] CORS corrected to the exact production origin, no trailing slash.
- [ ] Any base URL used to build shareable links points at production.
- [ ] Auth provider site URL and redirect URLs include the production domain.
- [ ] Redeploy triggered where the platform needs one, and it finished.

**Verify**
- [ ] Full happy path walked on the live URL, not localhost.
- [ ] Second browser or device used where multi-user behavior matters.
- [ ] Deep link refresh does not 404.
- [ ] Privacy and authorization invariants confirmed in production.

---

## 6. Ongoing maintenance

**Auto deploy is on.** `render.yaml` sets `autoDeploy: true`, and Vercel deploys
on push by default. So a push to `main` redeploys both. `.github/workflows/ci.yml`
runs the same four checks on push and on pull requests, but it does not gate the
deploy. A red CI run still ships. Treat local checks as the real gate.

**Changing a frontend env var** always needs a manual redeploy. See R2.

**Custom domain**, when you buy one:

1. Vercel, Project, Settings, Domains. Add it and set the DNS records at the
   registrar.
2. Update Render `CORS_ORIGINS` and `FRONTEND_BASE_URL` to the new domain.
3. Update Supabase Site URL and Redirect URLs.
4. Let the backend redeploy so it reads the new values.

Keep the old `.vercel.app` origin in `CORS_ORIGINS` during the transition, then
remove it once DNS has settled.

Optionally put the backend on `api.yourdomain.com` via Render, Settings, Custom
Domains, then update `VITE_API_BASE_URL` in Vercel and redeploy the frontend.

**Rotating a secret**: update it in the dashboard that owns it, then redeploy
that side. Rotating the Supabase JWT secret invalidates existing sessions, so
every signed-in user has to sign in again.
