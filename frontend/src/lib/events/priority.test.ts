import { describe, expect, it } from "vitest";

import {
  DAMAGE_CLASS,
  damageClassOf,
  sortEvents,
  type SortableEvent,
} from "./priority";

function event(
  partial: Partial<SortableEvent> & Pick<SortableEvent, "id">,
): SortableEvent {
  return {
    ts: 0,
    isActiveUnacked: false,
    damageClass: DAMAGE_CLASS.OTHER,
    ...partial,
  };
}

describe("damageClassOf", () => {
  it("maps canonical event name tokens to damage classes", () => {
    expect(damageClassOf("bearing_raznos_high")).toBe(DAMAGE_CLASS.RAZNOS);
    expect(damageClassOf("lube_oil_pressure_low")).toBe(DAMAGE_CLASS.OIL);
    expect(damageClassOf("exhaust_temp_high")).toBe(DAMAGE_CLASS.TEMP);
    expect(damageClassOf("generic_alarm")).toBe(DAMAGE_CLASS.OTHER);
  });
});

describe("sortEvents", () => {
  it("places active-unacked events before cleared/historical", () => {
    const sorted = sortEvents([
      event({ id: "cleared", isActiveUnacked: false, ts: 300 }),
      event({ id: "active", isActiveUnacked: true, ts: 100 }),
    ]);
    expect(sorted.map((e) => e.id)).toEqual(["active", "cleared"]);
  });

  it("orders active block by damage class разнос → масло → t°", () => {
    const sorted = sortEvents([
      event({
        id: "temp",
        isActiveUnacked: true,
        damageClass: DAMAGE_CLASS.TEMP,
        ts: 200,
      }),
      event({
        id: "raznos",
        isActiveUnacked: true,
        damageClass: DAMAGE_CLASS.RAZNOS,
        ts: 100,
      }),
      event({
        id: "oil",
        isActiveUnacked: true,
        damageClass: DAMAGE_CLASS.OIL,
        ts: 150,
      }),
    ]);
    expect(sorted.map((e) => e.id)).toEqual(["raznos", "oil", "temp"]);
  });

  it("within same class sorts by ts descending", () => {
    const sorted = sortEvents([
      event({
        id: "older",
        isActiveUnacked: true,
        damageClass: DAMAGE_CLASS.OIL,
        ts: 100,
      }),
      event({
        id: "newer",
        isActiveUnacked: true,
        damageClass: DAMAGE_CLASS.OIL,
        ts: 300,
      }),
      event({
        id: "mid",
        isActiveUnacked: true,
        damageClass: DAMAGE_CLASS.OIL,
        ts: 200,
      }),
    ]);
    expect(sorted.map((e) => e.id)).toEqual(["newer", "mid", "older"]);
  });

  it("keeps stable order when active, class, and ts are equal", () => {
    const sorted = sortEvents([
      event({
        id: "a",
        isActiveUnacked: true,
        damageClass: DAMAGE_CLASS.TEMP,
        ts: 50,
      }),
      event({
        id: "b",
        isActiveUnacked: true,
        damageClass: DAMAGE_CLASS.TEMP,
        ts: 50,
      }),
      event({
        id: "c",
        isActiveUnacked: true,
        damageClass: DAMAGE_CLASS.TEMP,
        ts: 50,
      }),
    ]);
    expect(sorted.map((e) => e.id)).toEqual(["a", "b", "c"]);
  });

  it("applies damage class then ts within cleared/historical block", () => {
    const sorted = sortEvents([
      event({
        id: "hist-temp-new",
        isActiveUnacked: false,
        damageClass: DAMAGE_CLASS.TEMP,
        ts: 900,
      }),
      event({
        id: "hist-raznos-old",
        isActiveUnacked: false,
        damageClass: DAMAGE_CLASS.RAZNOS,
        ts: 100,
      }),
      event({
        id: "active-oil",
        isActiveUnacked: true,
        damageClass: DAMAGE_CLASS.OIL,
        ts: 50,
      }),
    ]);
    expect(sorted.map((e) => e.id)).toEqual([
      "active-oil",
      "hist-raznos-old",
      "hist-temp-new",
    ]);
  });
});
