# Koodal — Task Backlog (for review before implementation)

> **Do not start coding until this backlog is reviewed and approved.**
> Tasks are grouped into milestones. Each has a rough size (S/M/L) and dependencies.
> IDs are stable so we can reference them in reviews and (later) commits.

Legend: **[S]** ≤half day · **[M]** ~1 day · **[L]** multi-day · `⟶` depends on.

---

## Milestone 0 — Foundations

| ID | Task | Size | Deps |
|----|------|------|------|
| T0.1 | Repo scaffold: `frontend/`, `backend/`, `supabase/`, `docs/`; root README | S | — |
| T0.2 | Supabase project (dev + prod), enable Google OAuth provider | S | — |
| T0.3 | Backend skeleton: FastAPI app, config via env, health route, structured logging (with budget-field redaction) | S | T0.1 |
| T0.4 | Frontend skeleton: Vite + React + Router + `supabase-js`, base layout, mobile-first styles | S | T0.1 |
| T0.5 | DB migration 0001: all tables + RLS from `03-lld.md §2` | M | T0.2 |
| T0.6 | CI: lint + test for both apps; Vercel preview wiring | S | T0.1 |

**Status (2026-08-18): Milestone 0 built & verified.**
- ✅ T0.1 repo scaffold + git init + `.gitignore`
- ✅ T0.3 FastAPI skeleton — `/api/health`, config, JSON logging with redaction (ruff clean, 3 tests pass)
- ✅ T0.4 Vite + React + Router + `supabase-js` skeleton, 4 routes, mobile-first CSS (typechecks + builds)
- ✅ T0.5 migration `0001_init.sql` — all tables + RLS (responses locked to service role)
- ✅ T0.6 GitHub Actions CI (backend: ruff+pytest · frontend: tsc+build)
- ✅ **T0.2 done:** Supabase project created, Google OAuth enabled, migration applied, both `.env` files filled. Backend health reports `supabase_configured: true`. Project uses the newer `sb_publishable/sb_secret` key format → JWTs are asymmetrically signed (verify via JWKS in T1.1).
- ℹ️ `npm audit` flags 4 advisories in dev-only tooling (vite/esbuild transitive); not runtime-facing. Revisit at T5.1.

## Milestone 1 — Create a catch-up (Flow 1)

| ID | Task | Size | Deps |
|----|------|------|------|
| T1.1 | Auth: verify Supabase JWT in FastAPI; `get_current_user` dependency | M | T0.3, T0.5 |
| T1.2 | `POST /api/catchups` + `slots` insert + token generation | M | T1.1 |
| T1.3 | `GET /api/catchups` and `GET /api/catchups/{id}` (owner) | S | T1.2 |
| T1.4 | Frontend: Google sign-in, auth context, protected routes | M | T0.4, T1.1 |
| T1.5 | Frontend: create-catch-up form (slots repeater, type, location, deadline) + validation | M | T1.4, T1.2 |
| T1.6 | Frontend: share screen (copy link, WhatsApp deep link, response counter) | S | T1.5 |

**Status (2026-08-19): Milestone 1 backend built & verified; frontend pending.**
- ✅ Tooling migrated to **uv** (`pyproject.toml` + `uv.lock`, `.venv`); requirements*.txt removed; Dockerfile + CI updated.
- ✅ T1.1 `app/core/auth.py` — Supabase JWT verify (JWKS for asymmetric keys + HS256 fallback, aud="authenticated"), `get_current_user`.
- ✅ T1.2 `POST /api/catchups` — profile upsert, catch-up + slots insert, 256-bit link/result tokens, invite/result URLs.
- ✅ T1.3 `GET /api/catchups` (list + response counts) and `GET /api/catchups/{id}` (owner-only, 404 on not-owned/missing).
- ✅ Repo layer `app/db/repo.py` (PostgREST via service role). 11 tests pass; ruff clean; **live DB reachability confirmed** across all 5 tables.
- ✅ T1.4 frontend Google sign-in (`lib/auth.tsx` AuthProvider/useAuth) + sign-in gate on `/new`.
- ✅ T1.5 create-catch-up form (title, type, location, message, slot repeater, deadline) with client validation.
- ✅ T1.6 share screen (`components/ShareScreen.tsx`) — copy link, WhatsApp deep link, link to results.
- Frontend typechecks + builds clean.
- ⚠️ Live create-path (real Google JWT → insert) needs manual E2E once OAuth redirect URLs are set in Supabase (see below).

## Milestone 2 — Respond privately (Flow 2)

| ID | Task | Size | Deps |
|----|------|------|------|
| T2.1 | `GET /api/invite/{link_token}` responder summary | S | T1.2 |
| T2.2 | `POST /api/invite/{link_token}/responses` (+ `response_slots`), empty success body | M | T2.1 |
| T2.3 | Validation: slot_ids belong to catch-up, budget_max≥min, closed/deadline guard | S | T2.2 |
| T2.4 | Light per-IP rate limit on response submit | S | T2.2 |
| T2.5 | Frontend: anonymous responder page — summary + form (slots, companions, budget range chips/slider, contribution, interests) | L | T0.4, T2.1 |
| T2.6 | Frontend: confirmation screen with privacy reassurance | S | T2.5 |

**Status (2026-08-19): Milestone 2 built & verified.**
- ✅ T2.1 `GET /api/invite/{link_token}` — summary with `creator_first_name` (first name only), no owner id/tokens. **Verified live** against real catch-up.
- ✅ T2.2 `POST /api/invite/{link_token}/responses` — inserts response + response_slots, returns only `{ok:true}` (no read side-channel).
- ✅ T2.3 validation — foreign slot_ids (422), budget_max≥min (422), closed (409), past deadline enforced (409, per OQ-7).
- ✅ T2.4 in-memory per-IP+token rate limit (10/min) — `app/core/ratelimit.py`.
- ✅ T2.5 responder page `routes/Respond.tsx` — summary, slot checkboxes, companions, budget preset chips, contribution, interest chips, privacy note.
- ✅ T2.6 confirmation screen with privacy reassurance + localStorage nudge.
- Backend: 20 tests pass (incl. "ack leaks nothing" privacy test), ruff clean. Frontend typechecks + builds.

## Milestone 3 — Matching, budget, suggestions (core logic)

| ID | Task | Size | Deps |
|----|------|------|------|
| T3.1 | `matching/` best-slot + alternatives + no-overlap; unit tests | M | T0.3 |
| T3.2 | `budget/` comfortable-group-budget + inclusion floor + rounding; unit tests incl. brief's 6/3/1 example | L | T0.3 |
| T3.3 | `suggestions/base.py` interface + `rules.py` catalogue + scoring; unit tests | M | T0.3 |
| T3.4 | Rationale templating | S | T3.1, T3.2 |
| T3.5 | Wire aggregator: `GET /api/catchups/{id}/results` (owner) + `GET /api/results/{result_token}` | M | T3.1–T3.4, T1.2 |
| T3.6 | Privacy contract test: assert no endpoint returns per-response private data (I1) | M | T3.5, T2.2 |

**Status (2026-08-19): Milestone 3 built & verified (incl. live).**
- ✅ T3.1 `matching/engine.py` — best-slot by weighted headcount, tie→earlier, no-overlap detection.
- ✅ T3.2 `budget/engine.py` — comfortable-group-budget (P60 of maxes), inclusion floor (70%), rounding. Brief's 6/3/1 outlier example proven: band holds at ₹500, outlier magnitude irrelevant.
- ✅ T3.3 `suggestions/{base,rules}.py` — provider interface + rules catalogue; never exceeds band high; cheapest option always included.
- ✅ T3.4 rationale templating.
- ✅ T3.5 `GET /api/catchups/{id}/results` (owner) + `GET /api/results/{result_token}` (shared). **Verified live** — computed a real result from 3 responses (group 8, band, suggestions, first-names-only).
- ✅ T3.6 privacy contract test — result payload has only aggregate keys; outlier's raw figures never appear.
- Backend: 37 tests pass, ruff clean.
- ⏳ Next: M4 results UI so this renders in the browser.

## Milestone 4 — Results UI (Flow 3)

| ID | Task | Size | Deps |
|----|------|------|------|
| T4.1 | Frontend: result card (best slot, group size, budget band + total, suggestions, rationale) | M | T3.5, T1.4 |
| T4.2 | Frontend: empty/low-data + no-overlap states | S | T4.1 |
| T4.3 | Frontend: share-result (copy + WhatsApp) using `result_token` | S | T4.1 |
| T4.4 | `POST /api/catchups/{id}/close` + UI toggle | S | T3.5 |

**Status (2026-08-19): Milestone 4 built.**
- ✅ T4.1 `routes/Result.tsx` result card — best slot, group size, budget band + total + inclusion %, contributions, suggestions, rationale, "responded" (first names).
- ✅ T4.2 empty state (waiting for responses) + no-overlap state (ranked alternatives).
- ✅ T4.3 share-result — copy link + WhatsApp deep link using the result URL.
- ✅ T4.4 `POST /api/catchups/{id}/close` (owner-only, 404 otherwise) + "Close responses" toggle on the share screen. 39 backend tests pass.
- Frontend typechecks + builds. **The full MVP loop (create → share → respond → results) is now implemented across all layers.**
- Note: no owner "my catch-ups" dashboard in MVP — close lives on the post-create share screen; results are opened via the shareable result link. Dashboard is a post-MVP nicety.

## Milestone 5 — Hardening & launch

| ID | Task | Size | Deps |
|----|------|------|------|
| T5.1 | CORS lockdown, secret handling review, error shape consistency | S | M1–M4 |
| T5.2 | E2E happy path test: create → respond ×N → results | M | M1–M4 |
| T5.3 | Deploy backend (container host) + Vercel prod; smoke test | M | T5.1 |
| T5.4 | Basic analytics/logging dashboards (counts only, no private fields) | S | T5.3 |
| T5.5 | Privacy copy pass + landing page explaining the promise | S | — |
| T5.6 | Anti-bot: honeypot + response cap (creator limit + server hard cap) | M | T2.2 |
| T5.7 | (Optional) Cloudflare Turnstile CAPTCHA on response submit | M | T5.6 |

**Status (2026-08-19): T5.6 done ahead of M5.**
- ✅ Migration `0002_response_limit.sql` adds `catchups.max_responses` (⏳ **apply in Supabase SQL editor**).
- ✅ Server response cap = `min(creator max_responses, RESPONSE_HARD_CAP=200)` → 409 when reached.
- ✅ Creator can set a response limit in the create form; server clamps to the hard cap.
- ✅ Honeypot `website` field — bots silently dropped, nothing stored.
- ✅ Backend 42 tests pass (incl. honeypot + cap); frontend builds.
- 🚫 T5.7 Turnstile **deferred by decision (2026-08-19)** — honeypot + rate limit + response cap deemed sufficient for the private link-shared MVP. Revisit only if real abuse appears.

---

## Critical path

```
T0.1 → T0.5 → T1.1 → T1.2 → {T2.1→T2.2}  ┐
                       └→ T3.1/T3.2/T3.3 → T3.5 → T4.1 → T5.2 → T5.3
```
Frontend milestones (T1.4–T1.6, T2.5–T2.6, T4.x) can proceed in parallel once their API deps land.

---

## Open questions — RESOLVED (2026-08-18)

All defaults accepted.

| ID | Question | **Decision** |
|----|----------|--------------|
| OQ-1 | First names to creator vs anonymous counts? | ✅ First names only, never answers |
| OQ-2 | Allow responders to edit later? | ✅ No for MVP (localStorage nudge only) |
| OQ-3 | Companions inherit budget band? | ✅ Inherit (LLD §5) |
| OQ-4 | Currency configurable? | ✅ INR only (config constant) |
| OQ-5 | `P_HIGH=60`, `INCLUSION_FLOOR=70%`? | ✅ Ship these, revisit with real data |
| OQ-6 | Backend host? | ✅ **Render** (free tier, simple env secrets; cold-start acceptable) |
| OQ-7 | Enforce deadline? | ✅ Enforce (reject after deadline) |

---

## UI overhaul (2026-08-19) — Material UI, elite light theme

Full frontend restyle to an Apple-inspired light design, before M5.
- **Stack:** MUI v9 (`@mui/material`) + `@mui/x-date-pickers` (MobileDateTimePicker) + `dayjs`. React upgraded to 19 (MUI v9 targets it). `react-router-dom` ^6.30.
- **Theme:** `src/theme.ts` — light palette (`#f5f5f7` bg, near-black text, Apple-blue accent), system/SF font stack, pill buttons, rounded surfaces. `CssBaseline` + `ThemeProvider` + `LocalizationProvider` in `main.tsx`.
- **Screens rebuilt:** Landing, NewCatchup (mobile date-time pickers), ShareScreen, Respond (chips + checkboxes), Result (sectioned card). Removed decorative emojis/arrows/dashes for a professional feel. Honeypot preserved (`styles.css .hp-field`).
- **MUI v9 gotchas (for future edits):**
  - System-prop shorthands were **removed** from `Stack`/`Typography` — put `alignItems`, `justifyContent`, `flexWrap`, `gap`, `display` in `sx`. `direction`/`spacing` remain direct props on `Stack`.
  - `TextField` renamed `inputProps` → `slotProps={{ htmlInput }}` and `InputProps` → `slotProps={{ input }}`.
- ✅ Typechecks + builds. No backend changes. Bundle ~286 KB gzip (MUI weight; code-split later if needed).

**Style pass (2026-08-19):** monochrome Apple palette (near-black `#1d1d1f` primary, white surfaces, gray text; no blue), elegant error styling (soft rose panel via `MuiAlert` `ownerState` overrides), all alert icons off. **Em dashes removed project-wide and banned going forward** (use periods/commas; en dashes fine in numeric ranges). MUI v9 note: combined style-override slots (`containedPrimary`, `standardError`, …) were removed — use `ownerState` callbacks in `styleOverrides.root`.

## Review checklist (sign off before coding)

- [ ] User flows in `01-user-flows.md` match the intended product
- [ ] Privacy invariants I1–I3 are acceptable and complete
- [ ] Budget algorithm (`03-lld.md §5`) produces the desired inclusive behaviour on the worked example
- [ ] Schema + API contracts approved
- [ ] Open questions OQ-1..OQ-7 answered
- [ ] Milestone ordering / scope agreed
