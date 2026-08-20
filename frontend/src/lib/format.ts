/** Human-friendly slot label, e.g. "Sat 5 Sep, 5:00–7:00 PM". */
export function formatSlot(startsAt: string, endsAt: string): string {
  const start = new Date(startsAt);
  const end = new Date(endsAt);
  const day = start.toLocaleDateString(undefined, {
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
  const day = d.toLocaleDateString(undefined, {
    weekday: "short",
    day: "numeric",
    month: "short",
  });
  const time = d.toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" });
  return `${day}, ${time}`;
}
