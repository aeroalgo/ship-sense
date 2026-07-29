import type { EventItem } from "@/lib/api/types";
import { damageClassOf, sortEvents } from "@/lib/events/priority";

export function isActiveUnacked(event: EventItem): boolean {
  if (event.severity !== "alarm") return false;
  if (event.params?.acked === true) return false;
  if (event.params?.cleared === true) return false;
  if (event.params?.lifecycle === "acked") return false;
  if (event.params?.lifecycle === "cleared") return false;
  return true;
}

export function sortJournalEvents(items: readonly EventItem[]): EventItem[] {
  const decorated = items.map((item) => ({
    item,
    id: item.id,
    isActiveUnacked: isActiveUnacked(item),
    damageClass: damageClassOf(item.event_name),
    ts: Date.parse(item.ts) || 0,
  }));
  return sortEvents(decorated).map((entry) => entry.item);
}
