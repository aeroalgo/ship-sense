import { describe, expect, it } from "vitest";

import { rollupNode, worstOf } from "./rollup";
import type { AggregateStatus, Quality } from "./types";

describe("worstOf", () => {
  it("returns unknown for empty input", () => {
    expect(worstOf([])).toBe("unknown");
  });

  it("returns the single quality when only one is provided", () => {
    expect(worstOf(["good"])).toBe("good");
    expect(worstOf(["quarantine"])).toBe("quarantine");
  });

  it("applies worst-of priority quarantine > stale > bad > uncertain > good", () => {
    const cases: Array<{ input: Quality[]; expected: AggregateStatus }> = [
      { input: ["good", "uncertain"], expected: "uncertain" },
      { input: ["uncertain", "bad"], expected: "bad" },
      { input: ["bad", "stale"], expected: "stale" },
      { input: ["stale", "quarantine"], expected: "quarantine" },
      {
        input: ["good", "uncertain", "bad", "stale", "quarantine"],
        expected: "quarantine",
      },
      { input: ["good", "stale", "uncertain"], expected: "stale" },
      { input: ["good", "bad"], expected: "bad" },
    ];

    for (const { input, expected } of cases) {
      expect(worstOf(input)).toBe(expected);
    }
  });

  it("quarantine beats good anywhere in the list", () => {
    expect(worstOf(["good", "good", "quarantine", "good"])).toBe("quarantine");
    expect(worstOf(["quarantine", "good"])).not.toBe("good");
  });
});

describe("rollupNode", () => {
  it("returns unknown when there are no children", () => {
    expect(rollupNode([])).toBe("unknown");
  });

  it("ignores unknown children when computing worst-of", () => {
    expect(rollupNode(["unknown", "good"])).toBe("good");
    expect(rollupNode(["unknown", "unknown"])).toBe("unknown");
  });

  it("rolls up group status as worst child", () => {
    expect(rollupNode(["good", "uncertain", "bad"])).toBe("bad");
  });

  it("quarantine anywhere makes group not good", () => {
    const status = rollupNode(["good", "good", "quarantine"]);
    expect(status).toBe("quarantine");
    expect(status).not.toBe("good");
  });
});
