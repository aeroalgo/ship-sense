import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

import {
  missingPublicEnvKeys,
  parseEnvExampleKeys,
  PUBLIC_ENV_KEYS,
} from "@/lib/env/public-env";

describe("scaffold smoke", () => {
  it("passes baseline assertion", () => {
    expect(true).toBe(true);
  });

  it("exposes the three public env keys from plan §4.4", () => {
    expect([...PUBLIC_ENV_KEYS]).toEqual([
      "NEXT_PUBLIC_API_URL",
      "NEXT_PUBLIC_WS_URL",
      "NEXT_PUBLIC_STALE_THRESHOLD_SEC",
    ]);
  });

  it(".env.example declares all public env keys", () => {
    const content = readFileSync(
      resolve(__dirname, "../../.env.example"),
      "utf8",
    );
    const keys = parseEnvExampleKeys(content);
    expect(missingPublicEnvKeys(keys)).toEqual([]);
  });
});
