-- Koodal — creator-settable response limit (docs/03-lld.md §7, anti-abuse)
-- The creator may cap how many responses a catch-up accepts. The backend also
-- enforces an absolute server-side upper bound (RESPONSE_HARD_CAP) regardless
-- of this value, so a large or tampered client value can't blow up the table.

alter table catchups
  add column if not exists max_responses int check (max_responses is null or max_responses > 0);
