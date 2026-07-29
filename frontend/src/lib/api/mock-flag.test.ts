import { describe, expect, it } from "vitest";

import { API_MOCK_ENV, isApiMockEnabled } from "@/lib/api/mock-flag";

describe("isApiMockEnabled", () => {
  it("is true only when NEXT_PUBLIC_API_MOCK=1", () => {
    expect(isApiMockEnabled({ [API_MOCK_ENV]: "1" })).toBe(true);
    expect(isApiMockEnabled({ [API_MOCK_ENV]: "0" })).toBe(false);
    expect(isApiMockEnabled({})).toBe(false);
  });
});
