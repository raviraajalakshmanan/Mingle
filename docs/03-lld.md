# Mingle: Low-Level Design (LLD)

Concrete contracts: database schema, API endpoints, the matching + budget algorithm, the suggestion engine, and security specifics. This is the document to nail down before coding.

---

## 1. Terminology

- **Catch-up** — an event a creator sets up.
- **Slot** — one discrete proposed time window (creator-defined).
- **Response** — one invitee's private answer.
- **Headcount for a response** — `1 + companions`.
- **Comfort range** — a response's `[budget_min, budget_max]` per-person spend.

---

## 2. Database schema (Postgres / Supabase)

```sql
-- 2.1 profiles: one row per authenticated creator (mirrors auth.users)
create table profiles (
  id           uuid primary key references auth.users(id) on delete cascade,
  display_name text,
  email        text,
  created_at   timestamptz not null default now()
);

-- 2.2 catchups
create table catchups (
  id           uuid primary key default gen_random_uuid(),
  owner_id     uuid not null references profiles(id) on delete cascade,
  title        text not null,
  message      text,
  location     text,                       -- free text in MVP
  type         text not null check (type in
                 ('casual','food','activity','outing','trip')),
  link_token   text not null unique,       -- opaque, >=128-bit, URL-safe
  result_token text not null unique,       -- separate token for read-only result share
  deadline     timestamptz,                -- optional
  status       text not null default 'open'
                 check (status in ('open','closed')),
  created_at   timestamptz not null default now()
);
create index on catchups (owner_id);

-- 2.3 slots: the discrete time options a responder can pick from
create table slots (
  id          uuid primary key default gen_random_uuid(),
  catchup_id  uuid not null references catchups(id) on delete cascade,
  starts_at   timestamptz not null,
  ends_at     timestamptz not null,
  label       text,                        -- optional pretty label
  sort_order  int not null default 0
);
create index on slots (catchup_id);

-- 2.4 responses: PRIVATE. never returned per-row via API.
create table responses (
  id             uuid primary key default gen_random_uuid(),
  catchup_id     uuid not null references catchups(id) on delete cascade,
  name           text not null,            -- first name / nickname
  companions     int  not null default 0 check (companions >= 0),
  budget_min     int  not null check (budget_min >= 0),   -- per person, minor unit-free (INR whole)
  budget_max     int  not null check (budget_max >= budget_min),
  contribution   int  not null default 0 check (contribution >= 0), -- optional group chip-in
  interests      text[] not null default '{}',
  created_at     timestamptz not null default now()
);
create index on responses (catchup_id);

-- 2.5 response_slots: which slots a given response is available for (many-to-many)
create table response_slots (
  response_id uuid not null references responses(id) on delete cascade,
  slot_id     uuid not null references slots(id) on delete cascade,
  primary key (response_id, slot_id)
);
```

### 2.6 Row-Level Security (defense in depth)
- Enable RLS on **all** tables.
- `responses` / `response_slots`: **no** client SELECT policy at all → the anon/authed client key can never read them. Only FastAPI's service role touches them.
- `catchups` / `slots`: SELECT allowed to owner (by `auth.uid()`); anonymous read is **not** granted via RLS — the responder summary is served by FastAPI using the token, so the client key needs no direct read. (Keeps the client key minimal.)
- Writes to all tables go through FastAPI (service role); no direct client writes.

> Net effect: even if the public anon key leaks, it cannot read anyone's budget.

---

## 3. API contracts (FastAPI)

Base URL `/api`. All JSON. Errors use `{ "error": { "code", "message" } }`.

### Auth modes
- **Creator endpoints:** `Authorization: Bearer <supabase-jwt>`; backend verifies signature + extracts `sub` = user id.
- **Anonymous endpoints:** authorized by the **link token** in the path; no JWT.

### 3.1 Create catch-up — creator
```
POST /api/catchups            (auth: creator JWT)
body {
  title, message?, location?, type,
  slots: [{ starts_at, ends_at, label? }, ...],   # >=1
  deadline?
}
201 → {
  id, link_token, result_token,
  invite_url: "https://app/r/<link_token>",
  result_url: "https://app/result/<result_token>"
}
```

### 3.2 List my catch-ups — creator
```
GET /api/catchups             (auth: creator JWT)
200 → [{ id, title, type, status, response_count, created_at }, ...]
```

### 3.3 Get catch-up (owner view) — creator
```
GET /api/catchups/{id}        (auth: creator JWT, must be owner)
200 → { id, title, message, location, type, status, deadline,
        slots:[...], response_count }        # NO raw responses
```

### 3.4 Get responder summary — anonymous
```
GET /api/invite/{link_token}                 (no auth)
200 → { title, message, location, type, creator_first_name,
        slots:[{ id, starts_at, ends_at, label }], deadline, status }
404 → unknown/closed token
```

### 3.5 Submit a response — anonymous
```
POST /api/invite/{link_token}/responses      (no auth)
body {
  name,
  slot_ids: [uuid, ...],          # subset of the catch-up's slots
  companions: int >= 0,
  budget_min: int, budget_max: int,   # per person
  contribution?: int,
  interests?: [string]
}
201 → { ok: true }                # deliberately returns NOTHING private
409 → catch-up closed / past deadline
422 → validation error
```
> Response body is intentionally empty of data — no echo of what was stored, so the endpoint can never become a read side-channel.

### 3.6 Get results — creator (or result token)
```
GET /api/catchups/{id}/results          (auth: creator JWT, owner)      # owner view
GET /api/results/{result_token}         (no auth)                       # shareable read-only
200 → {
  best_slot: { id, starts_at, ends_at, label, attending_headcount, attending_responses },
  alternatives: [ { slot..., attending_headcount }, ... ],   # ranked
  group_size: int,                        # headcount at best slot
  budget: {
    per_person: { low, high },
    total: { low, high },
    currency: "INR",
    inclusion_pct: number,                # % of attendees comfortable within band
    method: "comfortable-group-budget"
  },
  suggestions: [ { title, blurb, est_per_person: {low,high}, tags:[...] }, ... ],
  rationale: "Most people are free then, and this range works for almost everyone.",
  responded: [ "Rahul", "Priya", ... ]    # first names only — pending OQ-1
}
```
Empty states: `best_slot: null` + `message` when 0 responses or no overlap.

### 3.7 Close catch-up — creator
```
POST /api/catchups/{id}/close   (auth: creator JWT, owner)
200 → { status: "closed" }
```

---

## 4. Matching engine (`matching/`)

**Input:** all responses for a catch-up, each with `slot_ids`, `companions`.

**Best-slot selection**
```
for each slot s:
    attendees(s)   = responses where s in response.slot_ids
    headcount(s)   = sum over attendees of (1 + companions)
    people(s)      = count of attendees
best_slot = argmax over s of headcount(s)
tie-breakers, in order:  higher people(s)  →  earlier starts_at
```
- `group_size = headcount(best_slot)`.
- `alternatives` = other slots ranked by headcount desc (return top 2–3).
- **No overlap case:** if every slot has ≤1 attendee (or 0), return `best_slot = null`, expose the top slots as `alternatives` with their counts, and a message.

**Determinism:** pure function of the responses; no randomness → unit-testable with fixtures.

---

## 5. Budget engine (`budget/`) — the differentiator

**Goal:** a **comfortable group budget**, explicitly resistant to a single high outlier. Never `sum(max)` and never `mean`.

**Inputs:** for the attendees of the best slot, each response's `[budget_min, budget_max]` (per person) and `companions` (a companion inherits the responder's comfort band — MVP simplification).

### 5.1 Method (percentile-anchored inclusive band)

```
Let M = multiset of budget_max values, one entry per PERSON
        (responder counted, each companion counted with same band).
Let L = multiset of budget_min values, same weighting.

per_person.high = percentile(M, P_HIGH)      # P_HIGH = 60th percentile (config)
per_person.low  = percentile(L, P_LOW)        # P_LOW  = 30th percentile (config)
clamp so low <= high; if low > high, set low = min(L), high = per_person.high
round to nice numbers (nearest 50 or 100)

inclusion_pct = 100 * (# people whose budget_max >= per_person.high) / (total people)
```

**Why a percentile, not sum or mean.** The 60th percentile of the *maxes* is the price at which ~60% of people are still fully comfortable. A single ₹10,000 person is just one entry in `M`; they cannot move a 60th percentile. Summing maxima or averaging would let them inflate the plan — exactly the failure the product forbids.

**Worked example (from the brief):** 6 people @max 500, 3 @max 1000, 1 @max 10000 (10 people).
- Sorted `M` = [500×6, 1000×3, 10000].
- 60th percentile ≈ **500–800** → `per_person.high ≈ 800` (rounded), `per_person.low ≈ 400`.
- The ₹10,000 outlier changed nothing.
- `inclusion_pct` at high=800: people with max≥800 = the 3 @1000 + 1 @10000 = 4/10 = 40%. If inclusion drops below a floor (e.g. 70%), the engine **lowers `high`** to the value that meets the floor (here → 500, inclusion 100%). See 5.2.

### 5.2 Inclusion floor guard
```
INCLUSION_FLOOR = 0.70   # config
while inclusion_pct(per_person.high) < INCLUSION_FLOOR and can_lower:
    per_person.high = next_lower_distinct_max_below(current high)
recompute inclusion_pct
```
This makes inclusiveness the dominant force: the band settles at the highest price that still keeps ≥70% comfortable. The high-budget person can always spend more on themselves; the *recommendation* stays inclusive.

### 5.3 Totals
```
total.low  = per_person.low  * group_size
total.high = per_person.high * group_size
```
- **Contributions** (optional chip-ins) are summed separately and shown as "≈ ₹X already pledged toward shared costs" — they may *reduce* the effective per-person ask for shared items but **never raise** the recommended band. (MVP: display only; do not auto-adjust the band.)

### 5.4 Config (tunable, one file)
```
P_HIGH = 60, P_LOW = 30, INCLUSION_FLOOR = 0.70,
ROUND_TO = 50, CURRENCY = "INR"
```

### 5.5 Edge cases
- 1 response → band = that person's own range; inclusion 100%.
- All identical → low=high=that value.
- `budget_max = 0` allowed (free-only) → engine can recommend ₹0 activities.

---

## 6. Suggestion engine (`suggestions/`) — rules/templates (MVP)

Behind an interface `SuggestionProvider.suggest(context) -> [Suggestion]` so an AI provider can replace it later with no caller change.

**Context in:** `type`, `per_person band {low, high}`, `interests` (aggregated frequency across attendees), `group_size`, `location` (text, unused for filtering in MVP).

**Rules provider:** a curated catalogue keyed by `(type, budget_band, tags)`.
```
CATALOGUE = [
  { title:"Tea + walk",        types:[casual,activity], min:0,   max:300,  tags:[tea,walk] },
  { title:"Café + board games",types:[casual,food],     min:200, max:800,  tags:[games,food] },
  { title:"Park + snacks",     types:[casual,outing],   min:0,   max:400,  tags:[park] },
  { title:"Beach evening",     types:[outing],          min:0,   max:500,  tags:[beach,walk] },
  { title:"Dinner out",        types:[food],            min:400, max:1200, tags:[food] },
  { title:"Cricket/football + juice", types:[activity,sports], min:100, max:600, tags:[sports] },
  { title:"Day trip (shared cab)",    types:[trip,outing],     min:600, max:2500, tags:[trip] },
  ...
]
```
**Selection algorithm**
```
candidates = CATALOGUE where type matches AND band overlaps [low, high]
score = (interest_overlap_weight * matching_interest_tags)
      + (affordability_weight   * fits_within_high)
      + small tie-break by breadth (works for more of the group)
return top 2–4 by score, each with est_per_person and tags
```
**Rationale string** is templated: *"Most people are free {slot} and {band} works for almost everyone."*

**Guarantee:** suggestions never exceed `per_person.high`; the cheapest viable option is always included so no one is priced out.

---

## 7. Security specifics

- **Tokens:** `secrets.token_urlsafe(32)` (256-bit). Separate `link_token` (respond) and `result_token` (view) so sharing a result never grants response ability.
- **JWT verification:** validate Supabase JWT signature (JWKS/HS depending on project), check `exp`, extract `sub`. Reject otherwise.
- **Authorization:** every creator endpoint re-checks `catchup.owner_id == sub`. Never trust an id from the client alone.
- **Input validation:** Pydantic models; `slot_ids` must belong to the catch-up; `budget_max >= budget_min`; clamp absurd values (e.g. cap at a sane max).
- **No side-channels:** response POST returns no stored data; results endpoint returns only aggregates; there is no per-response GET anywhere.
- **Logging:** structured logs exclude `budget_*`, `contribution`, `interests`, `name`. Log ids and counts only.
- **Rate limiting (light):** per-IP cap on response submits per token to blunt spam.
- **Response cap (anti-pollution):** every catch-up accepts at most `min(creator max_responses, RESPONSE_HARD_CAP)` responses; over that → 409. `RESPONSE_HARD_CAP` (default 200) is a server-side upper bound the client cannot exceed.
- **Honeypot:** responses carry a hidden `website` field; any non-empty value is treated as a bot and silently dropped (stored nothing, bot gets a normal-looking ack).
- **CAPTCHA (optional, recommended for public launch):** Cloudflare Turnstile token verified server-side on submit. Deferred pending account setup.
- **CORS:** allow only the Vercel origin(s).

> Bot-defense layers, cheapest first: honeypot → per-IP rate limit → response cap → (optional) Turnstile. The first three ship now; the cap alone bounds worst-case DB growth per catch-up.

---

## 8. Testing plan (what proves it works)

| Area | Test |
|------|------|
| Privacy I1 | Assert no route returns per-response budget/slots (contract test + code scan) |
| Budget outlier | Brief's 6/3/1 example → band stays ₹400–800, outlier ignored |
| Inclusion floor | Skewed input → high lowered until ≥70% comfortable |
| Matching | Fixtures for clear winner, tie (→ earlier), no-overlap (→ null + alternatives) |
| Headcount | Companions summed correctly into group_size |
| Suggestions | Never exceed `per_person.high`; cheapest option always present |
| Auth | Non-owner blocked from results; missing token blocked from respond |
| Validation | `budget_max < budget_min`, foreign slot_ids, closed/expired catch-up |

---

## 9. Repository layout (proposed)

```
mingle/
├── docs/                 # these planning docs
├── frontend/             # React + Vite
│   └── src/{routes,components,lib(supabase,api)}
├── backend/              # FastAPI
│   └── app/
│       ├── main.py
│       ├── api/{catchups,invite,results}.py
│       ├── core/{auth,config,db,logging}.py
│       ├── models/       # Pydantic + DB access
│       ├── matching/
│       ├── budget/
│       └── suggestions/{base.py, rules.py}   # ai.py later
└── supabase/migrations/  # SQL from §2
```
