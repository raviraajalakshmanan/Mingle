# MigleUp: Internationalisation (markets, currency, activity catalogue)

Status: **draft for review, 2026-08-21.** Written before design, to be signed off
first. Supersedes the Milestone 6 sketch in `04-tasks.md` and resolves OQ-4
("INR only") for good.

---

## 1. The problem

MigleUp currently assumes one country. Rupees are hardcoded at seven UI sites, the
budget brackets are rupee amounts, and the suggestion catalogue is built from
chai, cricket, beaches, and shared cabs. None of that survives contact with a
user in Osaka or Guadalajara.

The trap is that this looks like a formatting problem and is not one. A catch-up
is **one shared link feeding one aggregate**. If a creator sets a `₹500-1000`
band and an invitee's browser renders it as `$500-1000`, that invitee answers a
different question, and their answer is averaged in as though it were the same
unit. The budget algorithm silently produces a band that is wrong for everyone,
and nothing in the interface reveals it. That is data corruption wearing the
costume of a display bug.

So the rule is:

> **Currency is a property of the catch-up, chosen once by the creator, frozen at
> creation, and rendered identically for every viewer. It never follows the
> viewer.**

This is deliberately the **opposite** of how we handled time. Slot times follow
the viewer, because an instant is objective and each person needs it in their own
frame. A price is a shared contract in a unit the creator picked. Two problems
that look alike, with opposite answers. Anyone who "fixes" currency by copying
the timezone pattern reintroduces the bug.

Converting brackets by exchange rate does not work either. `₹200-500` is about
`$2.40-6.00`, which is arithmetically correct and useless: no American picks
"$2.40 to $6.00" as a night out. Brackets have to be **authored per currency** in
round, locally legible numbers.

---

## 2. Scope

Target markets: **India, Japan, United States, Mexico, and Europe.**

Reducing scope means limiting *currencies*, not countries. Two phases:

| Phase | Currencies | Countries covered |
|---|---|---|
| **1** | INR, USD, EUR, GBP, JPY, MXN | India, US, all 20 eurozone countries, UK, Japan, Mexico |
| **2** | CHF, SEK, NOK, DKK, PLN, CZK, HUF, RON, BGN | Switzerland, Sweden, Norway, Denmark, Poland, Czechia, Hungary, Romania, Bulgaria |

Six currencies in Phase 1 cover every target market and the large majority of
European population. The honest cost of that cut: a creator in Warsaw gets EUR as
their default until Phase 2. They can still pick from the six, so they are not
blocked, only served something slightly foreign. That is an acceptable launch
compromise and a bad permanent state.

**Not in scope, deliberately:** multiple currencies inside one catch-up, and live
FX conversion. Both destroy the single shared aggregate the budget algorithm
depends on. Splitting a bill across countries is a different product, not a
formatting feature.

---

## 3. Categories: what people actually organise

Today the app has one axis, `type` (`casual`, `food`, `activity`, `outing`,
`trip`), chosen by the creator, plus responder-selected `interests`
(`tea/coffee`, `food`, `walk`, `park`, `beach`, `games`, `sports`, `day-trip`).

Research across the target markets says one axis is not enough, because **who you
are with predicts spend and suitability more strongly than what you do.** A
"food" catch-up means a 900 yen ramen counter with two friends or a 12,000 yen
table with in-laws. Same type, different planet.

So add a second axis.

### Axis A: occasion type (exists, keep)

`casual`, `food`, `activity`, `outing`, `trip`.

### Axis B: group context (new)

| Value | Who | Effect on spend and suggestions |
|---|---|---|
| `friends` | Peer group, splitting evenly | Widest spread. Default. |
| `family` | Mixed ages, often children | Daytime, seated, kid-viable, lower per-head ceiling but higher headcount |
| `couples` | Two to three couples | Skews to sit-down meals and evenings |
| `colleagues` | Work, semi-formal | Neutral venues, drinks or lunch, avoids the very cheap and the very personal |
| `mixed` | Large or unknown | Widest inclusion, safest options |

`family` is the one that most changes output: it should bias toward daytime,
seating, and venues that tolerate children, and it raises expected headcount,
which the budget engine already handles through companions.

---

## 4. The activity spine

Rather than a catalogue per country, define **twelve universal archetypes** and
give each market its own local instances. The archetype carries the structure
(price tier, group context fit, time of day), the instance carries the words.

| # | Archetype | Tier | Fits context |
|---|---|---|---|
| A1 | Coffee or tea catch-up | 1-2 | all |
| A2 | Walk, park, or waterfront | 1 | all, strong for family |
| A3 | Home gathering or potluck | 1-2 | friends, family |
| A4 | Casual meal out | 2-3 | all |
| A5 | Street food or market crawl | 1-2 | friends, couples |
| A6 | Proper sit-down dinner | 3-4 | couples, colleagues, family |
| A7 | Drinks or bar evening | 3-4 | friends, colleagues |
| A8 | Games, bowling, arcade | 2-3 | friends, family |
| A9 | Sport, played or watched | 2-4 | friends |
| A10 | Culture: museum, gallery, live event | 2-4 | couples, family |
| A11 | Cinema | 2-3 | all |
| A12 | Day trip or excursion | 4-5 | friends, family |

### Local instances

| Archetype | India | Japan | United States | Mexico | Europe |
|---|---|---|---|---|---|
| A1 | Chai and a stroll | Kissaten or chain café | Coffee shop | Café de olla, panadería | Café, terrace |
| A2 | Beach evening, park | Hanami, riverside, park | Trail hike, park | Parque, malecón | Park picnic, riverside, coastal walk |
| A3 | Home potluck | Takonomiyaki or nabe party | Potluck, backyard | Carne asada at home | Dinner party, apéro at home |
| A4 | Thali, casual restaurant | Ramen, teishoku, family restaurant | Diner, brunch, casual restaurant | Comida corrida, fonda | Bistro, trattoria, pub lunch |
| A5 | Street food crawl | Depachika, yatai, konbini picnic | Food truck, food hall | Taquería, mercado | Market hall, street food quarter |
| A6 | Sit-down dinner out | Izakaya course, sushi | Dinner out | Restaurante, cena | Restaurant dinner |
| A7 | Cafe or lounge evening | Izakaya, nomikai, standing bar | Brewery, bar, cocktails | Cantina, mezcalería | Pub, beer garden, aperitivo, wine bar |
| A8 | Board game cafe, arcade | Game center, karaoke, bowling | Bowling, arcade, board game bar | Boliche, billar | Board game café, bowling, karaoke |
| A9 | Cricket or football, then juice | Batting cage, baseball match | Pickup game, ballgame | Fútbol, lucha libre | Football match, padel, bouldering |
| A10 | Museum, live music | Museum, onsen or sento, festival | Museum, live music, comedy | Museo, zócalo events | Museum, gallery, concert, Christmas market |
| A11 | Multiplex | Cinema | Movie theater | Cine | Cinema |
| A12 | Day trip, shared cab | Day trip by train, hot spring town | Road trip, state park | Pueblo mágico, balneario | Train day trip, nearby town, coast |

Two content notes. **Karaoke and onsen carry real social weight in Japan** and
have no US equivalent, so Japan's catalogue is not a translation. **Mexico's
`family` context is heavier than elsewhere**, so weight A3 and A2 upward there.

---

## 5. Brackets

Keep the existing five-bucket shape. Define the tiers **semantically**, then
author round local numbers that land on each anchor. That is what makes brackets
portable without FX.

| Tier | Anchor: "what this buys one person" |
|---|---|
| 1 | Free or nearly. A coffee at most. |
| 2 | Coffee and a snack, or street food. |
| 3 | A casual meal out. |
| 4 | A proper dinner, or a ticketed activity. |
| 5 | A premium evening or a day trip. |

### Phase 1 tables

| Currency | Tier 1 | Tier 2 | Tier 3 | Tier 4 | Tier 5 |
|---|---|---|---|---|---|
| INR | 0-200 | 200-500 | 500-1,000 | 1,000-2,000 | 2,000+ |
| USD | 0-10 | 10-25 | 25-50 | 50-100 | 100+ |
| EUR | 0-10 | 10-25 | 25-50 | 50-100 | 100+ |
| GBP | 0-10 | 10-20 | 20-40 | 40-80 | 80+ |
| JPY | 0-1,000 | 1,000-2,500 | 2,500-6,000 | 6,000-12,000 | 12,000+ |
| MXN | 0-150 | 150-350 | 350-800 | 800-1,500 | 1,500+ |

INR is unchanged, so nothing already in production shifts.

### Phase 2 tables (draft)

| Currency | Tier 1 | Tier 2 | Tier 3 | Tier 4 | Tier 5 |
|---|---|---|---|---|---|
| CHF | 0-15 | 15-30 | 30-60 | 60-120 | 120+ |
| SEK | 0-100 | 100-250 | 250-500 | 500-1,000 | 1,000+ |
| NOK | 0-120 | 120-300 | 300-600 | 600-1,200 | 1,200+ |
| DKK | 0-75 | 75-175 | 175-400 | 400-800 | 800+ |
| PLN | 0-30 | 30-75 | 75-150 | 150-300 | 300+ |
| CZK | 0-200 | 200-500 | 500-1,000 | 1,000-2,000 | 2,000+ |
| HUF | 0-2,000 | 2,000-5,000 | 5,000-10,000 | 10,000-20,000 | 20,000+ |
| RON | 0-40 | 40-100 | 100-200 | 200-400 | 400+ |
| BGN | 0-15 | 15-40 | 40-80 | 80-160 | 160+ |

### Evidence: price anchors, Numbeo, August 2026

Every table above was checked against real per-country prices rather than left as
an estimate. "Mid-range per person" is Numbeo's three-course meal for two,
halved.

| Currency | Coffee | Cheap meal | Mid-range per person | Cinema | Beer 0.5L |
|---|---|---|---|---|---|
| INR | 163 | 200 | 500 | 300 | 180 |
| JPY | 496 | 1,000 | 2,500 | 2,000 | 500 |
| USD | 5.46 | 20 | 40 | 15 | 6 |
| MXN | 65 | 200 | 400 | 95 | 50 |
| EUR, Germany | 3.61 | 15 | 32.60 | 13 | 4.50 |
| EUR, France | 3.43 | 15 | 30 | 12 | 6 |
| EUR, Spain | 2.13 | 15 | 25 | 8.50 | 3 |
| EUR, Portugal | 1.88 | 12 | 22.50 | 8 | 2.50 |
| GBP | 3.58 | 16 | 32.50 | 10 | 5 |
| CHF | 5.11 | 25 | 50 | 20 | 7.40 |
| SEK | 46 | 145 | 400 | 159 | 80 |
| NOK | 53 | 220 | 500 | 175 | 110 |
| DKK | 43 | 150 | 350 | 130 | 55 |
| PLN | 14 | 40 | 95 | 30 | 15 |
| CZK | 68 | 200 | 500 | 240 | 50 |
| HUF | 845 | 4,000 | 9,000 | 2,750 | 900 |
| RON | 13 | 50 | 102 | 37.50 | 11 |
| BGN | 4.35 | 20 | 40 | 15 | 4 |

Source: Numbeo country cost-of-living pages, retrieved 2026-08-21.

**Result: 14 of the 15 drafted tables survived unchanged.** Only DKK moved, where
tier 3 had landed exactly on the mid-range anchor of 350 kr; its top is now 400.

Three findings worth carrying into design:

1. **One EUR table is defensible for all 20 eurozone countries.** The spread from
   Portugal to Germany is only about 1.25x on a cheap meal. The gap that would
   break a shared table does not exist inside the eurozone. It exists between the
   eurozone and the non-euro east, which is exactly where Phase 2 currencies are.
2. **CZK lands on the identical table to INR** (0-200 / 200-500 / 500-1,000 /
   1,000-2,000 / 2,000+) despite very different economies. Tables can be shared
   between currencies where the anchors agree, so the count of tables to maintain
   is smaller than the count of currencies.
3. **Japan prices cinema unusually high** relative to food, at 2,000 yen against a
   1,000 yen cheap meal, the reverse of most markets. Archetype A11 needs a
   Japan-specific cost, not an inherited one. This is concrete evidence for why
   catalogue costs are authored per market rather than converted.

Remaining uncertainty is now about **wording and cultural fit**, not amounts. The
activity instances in section 4 are still my draft and are the part most worth a
native speaker's eye before Phase 3.

Catalogue costs in `rules.py` inherit the same problem: `min_cost` and `max_cost`
are bare integers that are implicitly rupees today. Each currency needs its own
authored costs, not converted ones.

---

## 6. Currency selection

### Detection, and its one legitimate use

Detect from the browser's IANA timezone at **creation time only**:

```
Intl.DateTimeFormat().resolvedOptions().timeZone   // "Asia/Kolkata"
```

Map zone to country to currency. Fall back to **USD** when the zone is unknown or
unmapped.

**Why timezone and not `navigator.language`.** Language is a poor proxy for
place: `en-US` is extremely common on phones in Germany, India, and Japan.
Timezone tracks physical location far more reliably, and it is the correct signal
here.

**Why this is safe despite section 1.** Only creators authenticate. Responders
are anonymous and never sign in, so "detect at login" scopes naturally to exactly
the one person entitled to choose. Detection produces a **pre-filled default that
the creator can change**, and the choice is written to the catch-up on save.
After that it is a stored fact, never re-derived.

Three rules make the difference between a default and the bug:

1. Detection runs on `NewCatchup` only, never on `Respond` or `Result`.
2. The picker is visible on the create form, not buried. A creator in Tokyo
   planning a Bangalore meetup must be able to override without hunting.
3. Once written, the value is read from the catch-up forever.

### Mapping sketch

| Timezone | Currency |
|---|---|
| `Asia/Kolkata` | INR |
| `Asia/Tokyo` | JPY |
| `America/Mexico_City`, other `America/*` Mexican zones | MXN |
| `America/*` US and Canadian zones | USD |
| `Europe/London` | GBP |
| `Europe/Zurich` | CHF (Phase 2, EUR until then) |
| `Europe/Stockholm`, `Oslo`, `Copenhagen`, `Warsaw`, `Prague`, `Budapest`, `Bucharest`, `Sofia` | own currency in Phase 2, EUR until then |
| Other `Europe/*` | EUR |
| Anything unmapped | USD |

Note the asymmetry, which is intentional: **new** catch-ups with an unknown zone
fall back to USD, while **existing rows** backfill to INR, because every
catch-up in production today is Indian.

---

## 7. Requirements

### Functional

- **R1** A catch-up stores exactly one currency, set at creation.
- **R2** The create form pre-selects a currency from the creator's timezone,
  falling back to USD, and lets the creator change it before saving.
- **R3** Every viewer of a catch-up sees its currency, regardless of their own
  locale, language, or timezone.
- **R4** Budget brackets come from a per-currency table authored by hand, served
  by the API, never computed client-side and never FX-converted.
- **R5** The responder screen renders brackets in the catch-up's currency.
- **R6** The result screen renders the band, totals, contributions, and
  suggestion costs in the catch-up's currency.
- **R7** The server returns amounts and a currency code. It never formats money
  into a display string.
- **R8** Suggestions are drawn from a catalogue matched to the catch-up's
  currency and market, with costs authored in that currency.
- **R9** The creator picks a group context (`friends`, `family`, `couples`,
  `colleagues`, `mixed`), defaulting to `friends`.
- **R10** Suggestions are filtered and ranked by group context as well as type,
  budget, and interests.
- **R11** Interest tags are market-appropriate, replacing the current fixed
  India-flavoured list.

### Invariants

- **I4 (new)** Currency is immutable once the first response exists. `budget_min`
  and `budget_max` are stored as bare integers with no unit, so changing currency
  afterwards silently reinterprets every stored response. Block the edit, or
  treat a change as closing the catch-up and opening a new one.
- **I5 (new)** No currency symbol is ever hardcoded in a component. All money
  rendering goes through one formatter that takes an explicit currency.
- **I1 (unchanged)** Aggregate-only results. Nothing here adds a per-person
  disclosure, and the currency work must not introduce one.

### Non-functional

- **R12** Existing catch-ups keep behaving identically. INR brackets do not move,
  and the migration backfills INR.
- **R13** Adding a currency means adding a bracket table and a catalogue. It must
  require no changes to the budget algorithm.
- **R14** Money formatting uses `Intl.NumberFormat` with an **explicit** currency
  and an explicit locale derived from the catch-up, not from the viewer.
- **R15** A test asserts that no bare currency symbol appears in any component.

---

## 8. Plan

**Phase 0, foundations.** Migration `0003`: add `currency` and `group_context` to
`catchups`, defaulting to `INR` and `friends`. Thread currency from the catch-up
into `compute_band`. Delete the `CURRENCY` constant in `budget/engine.py:16` so
no ambient default can hide a missing value.

**Phase 1, brackets and rendering.** Author the six Phase 1 bracket tables in a
new `backend/app/budget/bands.py`. Serve brackets in the invite payload. Build
`formatMoney(amount, currency)` in `lib/format.ts` and replace all seven
hardcoded `₹` sites. Strip `₹` from the rationale in `api/results.py:123`.

**Phase 2, creation.** Timezone to currency map, currency picker on `NewCatchup`,
group context picker. Enforce invariant I4.

**Phase 3, content.** Restructure `rules.py` around the twelve archetypes, author
per-market catalogues with local costs and local wording, and make suggestions
context-aware. This is the largest and least technical phase, and it is the one
that decides whether the app feels native or translated.

**Phase 4, second wave.** The nine Phase 2 currencies, once the shape is proven.

Sequencing note: Phases 0 and 1 are pure refactors with no user-visible change
beyond correctness, so they can ship independently and de-risk the rest.

---

## 9. Open questions, to answer before design

- **OQ-8** Is `group_context` a creator choice, or inferred from type? Creator
  choice is proposed. It adds a field to an already busy form.
- **OQ-9** Do we localise language too, or is English-only acceptable at launch?
  This spec assumes English copy with local *content*, which is a real product
  bet worth making consciously.
- **OQ-10** Should a creator be able to pick any of the six currencies, or only
  the one detected? Proposed: any, since diaspora and travel are common.
- **OQ-11** Bracket amounts are now validated against Numbeo (section 5). Still
  open: who sanity-checks the **activity wording** per market, which is the part
  that decides whether the app reads as native or translated?
- **OQ-12** Does `family` context need child-friendly filtering strong enough to
  hide venues, or is ranking sufficient? Ranking is proposed.
