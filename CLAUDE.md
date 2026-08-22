# CLAUDE.md - MigleUp

Guidance for Claude working on this repo. Read this first, then `docs/` for depth.

## What this app is

**MigleUp** is a private, low-pressure way to plan a group catch-up without anyone
revealing what they can afford. One person creates a catch-up and shares a link.
Each invitee privately picks available times, how many people they are bringing,
and a comfortable spending range. Nobody sees anyone else's availability or budget.
MigleUp finds the best overlap of time + group size + an inclusive budget, and
suggests a few affordable things to do.

Core principle: the app helps people meet without making money the reason they
cannot meet.

## Hard rules (do not break)

1. **Never use the em dash character anywhere** (UI text, comments, docs, chat).
   Use periods or commas. En dashes in numeric ranges (for example "5-7 PM",
   budget bands) are fine.
2. **Monochrome Apple foundation, brand gradient as a limited accent.** Structure
   and text stay near-black `#1d1d1f` on white surfaces with gray `#6e6e73`
   secondary text. The purple-to-teal brand gradient is reserved for the logo, the
   single primary action on a screen, selected chips, and step numerals. Never
   blue. All styling flows from `frontend/src/theme.ts`, which exports `BRAND` and
   `brandGradient()`.
   **Colour is split by contrast role, do not mix the two pairs.** The vivid pair
   (`BRAND.purple` `#7824f0`, `BRAND.teal` `#00ccb4`) is sampled from the logo and
   is decorative only, never behind text: raw teal is 2.04:1 on white and fails
   WCAG. Anything carrying white text uses `brandGradient("action")`
   (`#6d1bd8` at 7.50:1 to `#0a7d70` at 5.02:1). Brand colour as text on white
   uses `BRAND.accent` `#5f17c4` (8.73:1).
3. **Errors render elegantly** as a soft rose panel (see `MuiAlert` overrides in
   the theme), never a loud red bar. Alerts have no icons.
4. **Privacy invariant (I1)**: no API path ever returns an individual response's
   budget or availability. Results are aggregate-only. Never add an endpoint or
   field that exposes per-person budget/slots. The `responses` table has no
   client read policy on purpose.
5. Keep it simple and elegant. Remove decorative icons/emojis and unnecessary
   punctuation.

## Tech stack

- **Frontend**: React 19 + Vite + TypeScript, Material UI v9 (`@mui/material`),
  `@mui/x-date-pickers` (MobileDateTimePicker) + dayjs, react-router-dom v6.
  Deploys to Vercel.
- **Backend**: FastAPI (Python), managed with **uv**. Talks to Supabase Postgres
  over PostgREST using the service role key; verifies Supabase JWTs (JWKS, with
  HS256 fallback). Deploys to Render (Docker).
- **Data/Auth**: Supabase Postgres + Google OAuth. Migrations in `supabase/migrations/`.

## Repository layout

```
backend/            FastAPI service (uv: pyproject.toml + uv.lock)
  app/
    main.py           app wiring, CORS, health
    core/             config, auth (JWT), db (PostgREST client), logging, ratelimit, tokens
    api/              catchups.py, invite.py, results.py
    matching/         best-slot selection
    budget/           comfortable-group-budget algorithm (the differentiator)
    suggestions/      base.py (interface) + rules.py (deterministic catalogue)
    models/schemas.py Pydantic request/response models
  tests/            pytest suite (42 tests)
  Dockerfile        uv-based image for Render
frontend/           React + Vite + MUI
  src/
    routes/           Landing, NewCatchup, Respond, Result
    components/        ShareScreen, HowItWorks
    lib/               api.ts, auth.tsx, supabase.ts, format.ts
    theme.ts           the single source of UI styling
  vercel.json       SPA rewrite so deep links work
supabase/migrations/  0001_init.sql, 0002_response_limit.sql
docs/               planning: overview, user flows, HLD, LLD, task backlog
render.yaml         Render blueprint for the backend
DEPLOYMENT.md       step-by-step deploy runbook (do this next)
```

## How to run locally

Prereqs: Node 20+ and npm, Python 3.11+ and `uv` (`brew install uv`), a Supabase
project with Google auth enabled and both migrations applied.

1. **Env files** (recreate from the examples; never commit them):
   - `backend/.env` from `backend/.env.example` (SUPABASE_URL, SUPABASE_SERVICE_KEY,
     SUPABASE_JWT_SECRET, CORS_ORIGINS, FRONTEND_BASE_URL). The service key and JWT
     secret are backend-only.
   - `frontend/.env.local` from `frontend/.env.example` (VITE_SUPABASE_URL,
     VITE_SUPABASE_ANON_KEY, VITE_API_BASE_URL=http://localhost:8000/api).
2. **Backend**: `cd backend && uv sync && uv run uvicorn app.main:app --reload`
   (serves at http://localhost:8000, health at /api/health).
3. **Frontend**: `cd frontend && npm install && npm run dev`
   (serves at http://localhost:5173).

## Checks (run before considering work done)

- Backend: `cd backend && uv run ruff check . && uv run pytest -q`
- Frontend: `cd frontend && npm run lint && npm run build`

## MUI v9 conventions (non-obvious)

- Layout shorthands were removed from `Stack`/`Typography`. Put `alignItems`,
  `justifyContent`, `flexWrap`, `gap`, `display` in `sx`. `direction`/`spacing`
  stay as direct `Stack` props.
- `TextField` uses `slotProps={{ htmlInput }}` (was `inputProps`) and
  `slotProps={{ input }}` (was `InputProps`).
- Combined style-override slots (`containedPrimary`, `standardError`, ...) were
  removed. Use `ownerState` callbacks inside `styleOverrides.root` (see theme.ts).

## Status

- Done: M0 foundations, M1 create, M2 respond, M3 matching/budget/suggestions,
  M4 results UI, anti-bot (honeypot + rate limit + response cap), MUI monochrome
  UI, rebrand to MigleUp.
- Next: **M5 - deploy** (see `DEPLOYMENT.md`). Also open in M5: finalize CORS to
  the prod origin, add an end-to-end happy-path test, optional analytics.
- Bot defense decision: honeypot + rate limit + response cap are enough for the
  MVP. Cloudflare Turnstile is deferred.

## Notes

- The product is named **MigleUp** in all code, package names, docs, and UI.
  Earlier working names (koodal, then Mingle) are retired in the codebase.
- **Infrastructure slugs still carry the old `mingle` name** and are deliberately
  left alone, because they identify live resources: the Render service
  `mingle-api`, its URL `https://mingle-api-bpnf.onrender.com`, the Vercel URL
  `https://mingle-ochre.vercel.app`, the GitHub repo `Mingle`, and the local repo
  folder. Renaming these is a dashboard operation, not a code change. Do it only
  when the user asks, and update `DEPLOY.md` plus `CORS_ORIGINS`,
  `FRONTEND_BASE_URL`, `VITE_API_BASE_URL`, and the Supabase redirect URLs in the
  same pass.
- Do not commit or push unless the user asks.
