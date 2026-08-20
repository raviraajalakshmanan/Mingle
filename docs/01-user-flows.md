# Koodal — User Flows

Three flows only. For each, the **privacy boundary** (what is visible vs. private) is called out explicitly, because privacy is the product.

Legend: 🟢 public/aggregated · 🔒 private (never shown to others).

---

## Actors

- **Creator** — starts the catch-up, signs in with Google, sees the aggregated result.
- **Responder (invitee)** — opens the link, answers privately, no account.

---

## Flow 1 — Create a catch-up

**Goal:** creator produces a shareable invite link in under a minute.

```
[Landing] → [Sign in with Google] → [New catch-up form] → [Created + share screen]
```

**Steps**

1. Creator lands on the site, taps **Create a catch-up**.
2. Signs in with Google (Supabase Auth). First sign-in auto-creates their profile.
3. Fills the **create form**:
   - Title / occasion — e.g. "Let's meet this Saturday evening"
   - **Proposed date/time options** — one or more discrete slots (e.g. Sat 5–7pm, Sat 7–9pm, Sun 11am–1pm). These are the *only* choices responders pick from.
   - Approximate **location** (free text for MVP — "Indiranagar", "near MG Road")
   - **Type** — casual catch-up / food / activity / outing / trip
   - Optional message
   - (Optional) response **deadline**
4. On submit, backend creates the catch-up + a random **link token**, returns the invite URL.
5. **Share screen** shows:
   - The invite URL with a copy button
   - A **"Share on WhatsApp"** button → opens `https://wa.me/?text=<encoded message + link>` (no WhatsApp API; just a deep link)
   - A **response counter** ("0 responded") that the creator can revisit anytime
   - A **"See results"** button (enabled once ≥1 response, or always with an empty state)

**Privacy boundary**

- The creator never enters anyone's budget. They only propose *when/where/what*.
- The invite link carries an **opaque token**, not a guessable ID.

---

## Flow 2 — Respond privately

**Goal:** an invitee answers in ~30s on their phone, no account, and trusts that their money info stays private.

```
[Open invite link] → [Catch-up summary] → [Private response form] → [Thank-you + reassurance]
```

**Steps**

1. Invitee opens the link (typically from WhatsApp). **No sign-in.**
2. Sees a **read-only summary** of the catch-up: title, proposed slots, location, type, creator's first name, message. 🟢
3. Fills the **response form**:
   - **Name** (or nickname) — shown to the group only as a count/first-name-level, see privacy note
   - **Available time slots** — multi-select from the creator's proposed slots 🔒
   - **How many people coming with them** — companions count (0+) 🔒
   - **Comfortable personal spending range** — a per-person range `[min, max]` via a slider/preset chips (e.g. ₹0–200, ₹200–500, ₹500–1000, ₹1000+) 🔒
   - **Optional contribution toward the group** — a one-off amount they'd chip in for shared costs (optional) 🔒
   - **Basic preferences / interests** — chips: tea/coffee, food, walk, park, beach, games, sports, day-trip 🔒
4. Submit. Backend stores the response against the token.
5. **Confirmation screen** with explicit reassurance: *"Your budget and availability are private. The organiser only sees the group's best option, never your individual answers."*

**Privacy boundary (critical)**

- Everything a responder enters is 🔒 **private**. It is **never** returned to the creator or to other responders through any endpoint.
- The only thing that becomes 🟢 is **aggregated output** (best slot, headcount, inclusive budget band, suggestions) and — a product decision below — possibly a **list of first names of who responded** (not their answers).
- **Decision needed at review:** do we show responders' first names to the creator ("Rahul, Priya, +6 responded")? Default: **yes, first names only, no answers**. Alternative: fully anonymous counts. See `04-tasks.md` open question OQ-1.

**Anti-abuse (MVP-light)**

- One response per browser is nudged via localStorage; a re-open pre-fills / offers "update my answer" if we adopt edit tokens (currently out — see OQ-2).
- Token in URL is required; without it the response API rejects.

---

## Flow 3 — Find the best meetup

**Goal:** turn the private responses into one clear, inclusive recommendation.

```
[Creator opens results] → [Backend runs matching] → [Result card] → [Share result]
```

**Steps**

1. Creator taps **See results** (or opens the results URL). Requires being the signed-in owner.
2. Backend runs the **matching engine** (`03-lld.md §Matching`) over all responses:
   - Picks the **best time slot** (max attendance, weighted by headcount).
   - Computes **group size** at that slot.
   - Computes an **inclusive per-person budget band** and a derived **total** using the *comfortable group budget* method — deliberately **not** the sum of maxima.
   - Runs the **suggestion engine** (rules/templates) to produce 2–4 concrete ideas fitting the type + budget band + interests.
3. **Result card** — example:

   > **Best option:** Saturday, 5–7 PM
   > **Group:** 8 people
   > **Recommended budget:** ₹400–800 per person (~₹1,500–2,500 total)
   > **Suggestions:** Tea + walk · Café + board games · Park + snacks
   > **Why:** Most people are free then, and this range works comfortably for almost everyone.

4. Creator can **share the result** (copy / WhatsApp deep link) so the group sees the plan.
5. Empty/low-data states: if 0 responses → "waiting for responses". If responses don't overlap on any slot → show top 2 partial slots with attendance.

**What the result MUST NOT say**

- ❌ "Rahul can spend ₹10,000 and Priya can spend ₹500."
- ✅ It reasons about the **group as a whole** and shows only bands + rationale.

**Privacy boundary**

- The result is aggregate-only. Even the owner cannot drill into an individual's budget or availability — there is no endpoint that returns it.

---

## Cross-flow diagram

```
 CREATOR                          SYSTEM                         RESPONDERS (xN, anonymous)
 ───────                          ──────                         ──────────
 sign in (Google) ─────────────►  create catch-up
                                  return invite link ──WhatsApp──►  open link
                                                                    view summary 🟢
                                                                    submit private answer 🔒
                                  store response ◄───────────────
 open results ───────────────►    run matching + suggestions
                 result card 🟢 ◄─ (best slot, size, inclusive
                                    budget band, ideas, rationale)
 share result ──WhatsApp────────►  group sees the plan
```
