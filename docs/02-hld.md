# MigleUp: High-Level Design (HLD)

Scope: the MVP three flows only. Aligns with decisions in `00-overview.md §8`.

---

## 1. Architecture overview

```
┌──────────────────────────────────────────────────────────────────┐
│                         Client (browser)                           │
│  React + Vite SPA, deployed on Vercel                              │
│                                                                    │
│  • Creator app  (authenticated)                                    │
│  • Responder page (anonymous, token in URL)                        │
│  • Result page  (owner + shareable read-only)                      │
└───────────────┬───────────────────────────────┬───────────────────┘
                │ Supabase JS (auth only)        │ HTTPS / REST (JSON)
                ▼                                 ▼
     ┌────────────────────┐          ┌───────────────────────────────┐
     │  Supabase Auth      │          │        FastAPI backend         │
     │  (Google OAuth)     │          │  (Python, containerised)       │
     │  issues JWT         │          │                                │
     └─────────┬───────────┘          │  • /catchups  (CRUD-lite)      │
               │ JWT verified          │  • /responses (anon submit)    │
               │ by FastAPI            │  • /results   (matching)       │
               │                       │                                │
               │                       │  Business logic:               │
               │                       │   - matching engine            │
               │                       │   - budget (comfortable group) │
               │                       │   - suggestion engine (rules)  │
               │                       └──────────────┬─────────────────┘
               │                                      │ SQL (service role)
               ▼                                      ▼
        ┌──────────────────────────────────────────────────────────┐
        │                 Supabase Postgres                         │
        │   profiles · catchups · slots · responses · response_slots│
        │   Row-Level Security enabled (defense in depth)           │
        └──────────────────────────────────────────────────────────┘
```

**Why this split** (decision 1): all privacy-sensitive logic and the matching/budget algorithm live server-side in one testable place (FastAPI). The client never runs matching and never receives raw responses. Supabase is used for what it is best at — managed Postgres + Google OAuth.

---

## 2. Components

### 2.1 Frontend (React + Vite → Vercel)
- **Three route groups:**
  - `/` , `/new`, `/c/:id` (creator, authenticated) — create + manage + view results
  - `/r/:token` (responder, anonymous) — summary + response form
  - `/result/:token` (read-only shareable result)
- Auth via `supabase-js` (Google). Access token attached as `Authorization: Bearer` on calls to FastAPI.
- No business logic; pure presentation + form validation. Mobile-first (responders arrive from WhatsApp).

### 2.2 Backend (FastAPI)
- Stateless REST service. Verifies Supabase JWTs for creator endpoints; verifies **link token** for anonymous endpoints.
- Talks to Postgres using the **service role** (bypasses RLS) but enforces its own authorization in code. RLS remains ON as a second wall.
- Houses three logic modules:
  - `matching/` — time-slot overlap
  - `budget/` — comfortable-group-budget computation
  - `suggestions/` — deterministic rules/templates
- Suggestion module is behind an interface so an AI implementation can be swapped in later without touching callers.

### 2.3 Data (Supabase Postgres)
- Five tables (see `03-lld.md §2`). RLS policies deny direct client reads of `responses`; only FastAPI (service role) reads them, and only to aggregate.

### 2.4 Share channel (WhatsApp)
- **No API integration.** Client builds a `https://wa.me/?text=...` deep link. This is purely a convenience; the security boundary is the link token, not WhatsApp.

---

## 3. Trust & privacy model (the heart of the design)

| Data | Who may read it | Enforced by |
|------|-----------------|-------------|
| Catch-up metadata (title, slots, location) | Creator + anyone with the link token | Token check + owner check |
| A response's raw budget/availability | **Nobody** via API — only the aggregator inside FastAPI | No endpoint exposes it; RLS blocks direct DB read |
| Aggregated result | Creator + anyone with the result token | Owner/token check |
| Responder identity | First name only (pending OQ-1) | Aggregation layer strips answers |

Key invariants:
- **I1:** There is **no** API path that returns an individual response's budget or slots.
- **I2:** Matching runs only server-side; the client receives only aggregates.
- **I3:** Link tokens are unguessable (≥128 bits, URL-safe).

---

## 4. Key technical decisions & trade-offs

| Decision | Chosen | Rejected | Why |
|----------|--------|----------|-----|
| Backend | FastAPI owns logic | Supabase Edge Functions | Testable algorithm, keeps privacy logic off the client, Python fits the (later) AI work |
| Suggestions | Rules/templates | AI in MVP | Deterministic, free, unit-testable; AI added later behind same interface |
| Responder auth | Anonymous + link token | Google sign-in for all | Lowest friction; core to "low-pressure" promise |
| DB access from FastAPI | Service role + in-code authz + RLS on | Per-user Postgres roles | Simpler; RLS is defense-in-depth |
| Time model | Discrete creator-defined slots | Free continuous availability | Vastly simpler matching; enough for MVP |

---

## 5. Non-functional requirements (MVP)

- **Privacy:** invariants I1–I3, covered by automated tests.
- **Performance:** results compute in <300 ms for ≤200 responses (pure in-memory aggregation).
- **Availability:** best-effort single-region; no HA requirement for MVP.
- **Cost:** near-zero — Supabase free tier, one small FastAPI container, Vercel hobby/pro.
- **Accessibility:** mobile-first, keyboard/tap friendly response form.
- **Observability:** structured request logs + basic error tracking; **never log raw budget values.**

---

## 6. Environments & deployment

- **Frontend:** Vercel (preview per PR + prod).
- **Backend:** container on **Render** (free tier; env-injected Supabase URL + service key + JWT secret). Cold-start on idle is acceptable for the MVP.
- **DB:** Supabase project (one for dev, one for prod). Migrations via SQL files in repo (`supabase/migrations/`).
- **Secrets:** Supabase service key + JWT signing secret live only in backend env, never in the client bundle.

---

## 7. Out of scope for HLD (deferred layers)

Maps, real place data, payments, chat, recurring groups, AI suggestions, native apps — all post-MVP. The suggestion interface and the DB schema leave room for them but nothing is built.
