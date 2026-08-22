# MigleUp: Product Overview & MVP Scope

> **Name:** MigleUp.
> **Status:** Planning. No implementation until the task backlog (`04-tasks.md`) is reviewed and approved.

---

## 1. The one-line idea

**A private, low-pressure way to get people together — without anyone having to reveal what they can afford.**

## 2. The problem

Group catch-ups stall on two invisible frictions:

1. **Scheduling** — finding a time that works for everyone.
2. **Money** — nobody wants to say "I can only spend ₹300" out loud, and nobody wants one person's big budget to set an expensive plan the others can't match.

Existing tools (When2Meet, Doodle, WhatsApp polls) solve time only. None handle the money question, and certainly not *privately*.

## 3. The core principle

> **The app helps people meet without making money the reason they can't meet.**

Everything in the design defers to this. Two hard rules fall out of it:

- **R1 — Privacy:** A person's availability and budget are **never** shown to the creator or to other participants. Only the aggregated result is visible.
- **R2 — Inclusive budgeting:** The recommended spend is driven by a **comfortable group budget**, not by the highest individual budget. One person able to spend ₹10,000 must **not** pull the group toward an expensive plan.

## 4. The differentiator

Private **budget + availability matching**. That is the only thing that is genuinely hard to copy and genuinely valuable. The MVP protects it and strips almost everything else.

---

## 5. MVP scope — exactly three flows

| # | Flow | Who | Auth |
|---|------|-----|------|
| 1 | **Create a catch-up** | Creator | Google sign-in |
| 2 | **Respond privately** | Each invitee | None (anonymous, per-link token) |
| 3 | **Find the best meetup** | Creator (+ shareable result) | Google sign-in |

Detailed step-by-step in `01-user-flows.md`.

## 6. Explicitly OUT of the MVP

Not building any of these in v1 (they are the "later" layers):

- Payments / splitting money
- In-app chat, comments, social feed
- Friend lists, rich profiles
- Maps / live restaurant / real place data (see AI note below)
- **AI-generated** suggestions — **MVP uses a deterministic rules/template engine.** AI is a later phase.
- Recurring groups, trips, multi-city
- Native mobile apps (web only; mobile-responsive)

## 7. Product roadmap (layers)

```
MVP   : Create → Share → Private responses → Find overlap → Suggest meetup (rules-based)
Later : Maps → Restaurants → Real activities → AI planning → Recurring groups → Trips → Payments
```

## 8. Decisions locked (2026-08-18)

1. **Architecture:** FastAPI owns all business logic; Supabase = Postgres + Google Auth only. (See `02-hld.md`.)
2. **Suggestions:** Deterministic rules/template engine for MVP; AI deferred.
3. **Responders:** Fully anonymous, secured by an unguessable per-catch-up link token. No responder account.
4. **Stack:** React + Vite (frontend, on Vercel) · FastAPI (backend) · Supabase Postgres + Auth · WhatsApp used only as a share channel (deep link, no API integration in MVP).

## 9. Success criteria for the MVP

- A creator can go from "create" to "shareable link" in under 60 seconds.
- A responder can answer on mobile in under 30 seconds, without an account.
- Given N responses, the result correctly (a) picks the best time slot, (b) reports group size, and (c) recommends an **inclusive** budget band that a documented test proves is not dragged up by a single high budget.
- No API response ever leaks an individual's budget or availability. (Verified by an automated privacy test.)

## 10. Document map

| File | Purpose |
|------|---------|
| `00-overview.md` | This file — vision, scope, principles, decisions |
| `01-user-flows.md` | The three flows, screen by screen, with privacy boundaries |
| `02-hld.md` | High-level design — architecture, components, data flow |
| `03-lld.md` | Low-level design — DB schema, API contracts, the matching + budget algorithm, security |
| `04-tasks.md` | Reviewable task backlog (do not start coding until approved) |
