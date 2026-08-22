# MigleUp

**Meet up, minus the money talk.**

MigleUp is a private, low-pressure way to plan a group catch-up without anyone
revealing what they can afford. One person creates a catch-up and shares a link.
Each invitee privately picks their available times, how many people they are
bringing, and a comfortable spending range. Nobody sees anyone else's
availability or budget. MigleUp then finds the best overlap of time, group size,
and an inclusive budget, and suggests a few affordable things to do.

> Core principle: the app helps people meet without making money the reason they
> cannot meet.

## Features

- **Create a catch-up** (Google sign-in): title, type, location, proposed time
  options, optional deadline, optional response limit. Get a shareable link.
- **Respond privately** (no account): pick times, companions, a comfortable
  budget, optional contribution and interests. Answers are never shown to others.
- **Best plan**: the app picks the time that works for the most people, computes
  an inclusive per-person budget band (resistant to a single high spender), and
  suggests affordable activities. Shareable result link.
- **Privacy first**: no endpoint ever returns an individual's budget or
  availability. Only aggregates are exposed.
- **Anti-abuse**: honeypot field, per-IP rate limit, and a response cap
  (creator-set, with a server-side upper bound).

## Tech stack

- **Frontend**: React 19 + Vite + TypeScript, Material UI v9, MUI X date pickers,
  dayjs, react-router-dom. Hosted on Vercel.
- **Backend**: FastAPI (Python), managed with uv. Hosted on Render (Docker).
- **Data/Auth**: Supabase Postgres + Google OAuth.

## Quick start (local)

### Prerequisites

- Node 20+ and npm
- Python 3.11+ and uv (`brew install uv`, or see https://docs.astral.sh/uv/)
- A Supabase project with Google auth enabled and both SQL migrations applied
  (`supabase/migrations/0001_init.sql`, then `0002_response_limit.sql`, run in the
  Supabase SQL editor)

### 1. Configure environment

Create the two env files from the examples (do not commit them):

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
```

Fill in the values from your Supabase project (Project Settings > API):

- `backend/.env`: `SUPABASE_URL`, `SUPABASE_SERVICE_KEY` (service role, backend
  only), `SUPABASE_JWT_SECRET`, `CORS_ORIGINS=http://localhost:5173`,
  `FRONTEND_BASE_URL=http://localhost:5173`
- `frontend/.env.local`: `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY` (public
  anon key), `VITE_API_BASE_URL=http://localhost:8000/api`

### 2. Run the backend

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
# http://localhost:8000  (health: /api/health)
```

### 3. Run the frontend

```bash
cd frontend
npm install
npm run dev
# http://localhost:5173
```

Open http://localhost:5173, sign in with Google, create a catch-up, then open the
invite link (works with no account) to respond, and view the result link.

## Tests and checks

```bash
# Backend
cd backend && uv run ruff check . && uv run pytest -q

# Frontend
cd frontend && npm run lint && npm run build
```

## Deploying

See `DEPLOYMENT.md` for the full step-by-step runbook (GitHub, Render backend,
Vercel frontend, Supabase auth URLs, and custom domain).

## Documentation

Design and planning live in `docs/`:

- `docs/00-overview.md` - vision, scope, principles
- `docs/01-user-flows.md` - the three user flows
- `docs/02-hld.md` - high-level architecture
- `docs/03-lld.md` - schema, API contracts, the matching and budget algorithm
- `docs/04-tasks.md` - task backlog and status

`CLAUDE.md` holds working conventions (style rules, MUI v9 notes, privacy
invariants) for anyone (including Claude) picking up the project.
