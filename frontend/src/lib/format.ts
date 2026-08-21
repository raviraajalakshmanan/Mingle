/**
 * Dates are always shown day-before-month (for example 5 Sep, 05/09/2026),
 * never the US month-first order, whatever locale the browser reports.
 * "en-GB" is used only to fix that order; times keep the browser's own
 * preference so 12 or 24 hour display stays familiar.
 */
const DAY_LOCALE = "en-GB";

/** Picker input mask, e.g. "05/09/2026 07:30 pm". */
export const DATE_TIME_FORMAT = "DD/MM/YYYY hh:mm A";

/** Human-friendly slot label, e.g. "Sat 5 Sep, 5:00–7:00 PM". */
export function formatSlot(startsAt: string, endsAt: string): string {
  const start = new Date(startsAt);
  const end = new Date(endsAt);
  const day = start.toLocaleDateString(DAY_LOCALE, {
    weekday: "short",
    day: "numeric",
    month: "short",
  });
  const t = (d: Date) =>
    d.toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" });
  return `${day}, ${t(start)} – ${t(end)}`;
}

/** Local start-time label for one slot, e.g. "Thu 20 Aug, 8:00 PM". */
export function formatSlotStart(startsAt: string): string {
  const d = new Date(startsAt);
  const day = d.toLocaleDateString(DAY_LOCALE, {
    weekday: "short",
    day: "numeric",
    month: "short",
  });
  const time = d.toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" });
  return `${day}, ${time}`;
}
