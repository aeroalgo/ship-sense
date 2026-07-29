export const DAMAGE_CLASS = {
  RAZNOS: "raznos",
  OIL: "oil",
  TEMP: "temp",
  OTHER: "other",
} as const;

export type DamageClass = (typeof DAMAGE_CLASS)[keyof typeof DAMAGE_CLASS];

export const DAMAGE_CLASS_RANK: Record<DamageClass, number> = {
  [DAMAGE_CLASS.RAZNOS]: 0,
  [DAMAGE_CLASS.OIL]: 1,
  [DAMAGE_CLASS.TEMP]: 2,
  [DAMAGE_CLASS.OTHER]: 3,
};

const EVENT_NAME_DAMAGE_CLASS: ReadonlyArray<{
  pattern: RegExp;
  damageClass: DamageClass;
}> = [
  { pattern: /raznos|imbalance|vibration|разнос/i, damageClass: DAMAGE_CLASS.RAZNOS },
  { pattern: /oil|lube|масло/i, damageClass: DAMAGE_CLASS.OIL },
  { pattern: /temp|temperature|t°|exhaust/i, damageClass: DAMAGE_CLASS.TEMP },
];

export type SortableEvent = {
  id: string;
  ts: number;
  isActiveUnacked: boolean;
  damageClass: DamageClass;
};

export function damageClassOf(eventName: string): DamageClass {
  for (const entry of EVENT_NAME_DAMAGE_CLASS) {
    if (entry.pattern.test(eventName)) {
      return entry.damageClass;
    }
  }
  return DAMAGE_CLASS.OTHER;
}

export function sortEvents<T extends SortableEvent>(events: readonly T[]): T[] {
  return events
    .map((event, index) => ({ event, index }))
    .sort((a, b) => {
      if (a.event.isActiveUnacked !== b.event.isActiveUnacked) {
        return a.event.isActiveUnacked ? -1 : 1;
      }

      const classDelta =
        DAMAGE_CLASS_RANK[a.event.damageClass] -
        DAMAGE_CLASS_RANK[b.event.damageClass];
      if (classDelta !== 0) {
        return classDelta;
      }

      if (a.event.ts !== b.event.ts) {
        return b.event.ts - a.event.ts;
      }

      return a.index - b.index;
    })
    .map(({ event }) => event);
}
