import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";

import { DesignSwitcher } from "@/components/ds/DesignSwitcher";
import {
  isDesignPreviewEnabled,
} from "@/lib/theme/switcher-spec";
import {
  readStoredDesign,
  writeStoredDesign,
} from "@/lib/theme/storage";
import {
  DEFAULT_DESIGN,
  STORAGE_DESIGN_KEY,
  nextDesign,
} from "@/lib/theme/types";

import { DesignProvider, useDesign } from "./DesignProvider";

function memoryStorage(initial: Record<string, string> = {}): Storage {
  const map = new Map(Object.entries(initial));
  return {
    get length() {
      return map.size;
    },
    clear() {
      map.clear();
    },
    getItem(key: string) {
      return map.has(key) ? map.get(key)! : null;
    },
    key(index: number) {
      return [...map.keys()][index] ?? null;
    },
    removeItem(key: string) {
      map.delete(key);
    },
    setItem(key: string, value: string) {
      map.set(key, value);
    },
  };
}

function DesignProbe() {
  const { design, setDesign, cycleDesign } = useDesign();
  return (
    <div>
      <span data-testid="design-value">{design}</span>
      <DesignSwitcher design={design} onChange={setDesign} enabled />
      <button type="button" data-testid="cycle-design" onClick={cycleDesign}>
        cycle
      </button>
    </div>
  );
}

describe("design storage + cycle", () => {
  afterEach(() => {
    cleanup();
  });

  it("defaults to d01 when storage empty", () => {
    const storage = memoryStorage();
    expect(readStoredDesign(storage)).toBe(DEFAULT_DESIGN);
    expect(readStoredDesign(storage)).toBe("d01");
  });

  it("rejects invalid storage values", () => {
    const storage = memoryStorage({ [STORAGE_DESIGN_KEY]: "d99" });
    expect(readStoredDesign(storage)).toBe("d01");
  });

  it("round-trips design through storage", () => {
    const storage = memoryStorage();
    writeStoredDesign("d03", storage);
    expect(readStoredDesign(storage)).toBe("d03");
    writeStoredDesign("d05", storage);
    expect(readStoredDesign(storage)).toBe("d05");
  });

  it("cycles d01 → d02 → … → d05 → d01", () => {
    expect(nextDesign("d01")).toBe("d02");
    expect(nextDesign("d02")).toBe("d03");
    expect(nextDesign("d03")).toBe("d04");
    expect(nextDesign("d04")).toBe("d05");
    expect(nextDesign("d05")).toBe("d01");
  });
});

describe("isDesignPreviewEnabled", () => {
  it("is true in development", () => {
    expect(isDesignPreviewEnabled({ NODE_ENV: "development" })).toBe(true);
  });

  it("is true when NEXT_PUBLIC_DESIGN_PREVIEW=1", () => {
    expect(
      isDesignPreviewEnabled({
        NODE_ENV: "production",
        NEXT_PUBLIC_DESIGN_PREVIEW: "1",
      }),
    ).toBe(true);
  });

  it("is false in production without preview flag", () => {
    expect(
      isDesignPreviewEnabled({
        NODE_ENV: "production",
        NEXT_PUBLIC_DESIGN_PREVIEW: "0",
      }),
    ).toBe(false);
  });
});

describe("DesignProvider", () => {
  let storage: Storage;

  beforeEach(() => {
    storage = memoryStorage();
    Object.defineProperty(window, "localStorage", {
      configurable: true,
      value: storage,
    });
    document.documentElement.removeAttribute("data-design");
  });

  afterEach(() => {
    cleanup();
    document.documentElement.removeAttribute("data-design");
  });

  it("applies stored design to html and persists switcher changes", () => {
    writeStoredDesign("d02", storage);
    render(
      <DesignProvider>
        <DesignProbe />
      </DesignProvider>,
    );

    expect(screen.getByTestId("design-value").textContent).toBe("d02");
    expect(document.documentElement.getAttribute("data-design")).toBe("d02");

    fireEvent.click(screen.getByTestId("design-switcher"));
    expect(screen.getByTestId("design-value").textContent).toBe("d03");
    expect(document.documentElement.getAttribute("data-design")).toBe("d03");
    expect(storage.getItem(STORAGE_DESIGN_KEY)).toBe("d03");
  });

  it("DesignSwitcher does not render when enabled=false", () => {
    function Gated() {
      const { design, setDesign } = useDesign();
      return (
        <DesignSwitcher design={design} onChange={setDesign} enabled={false} />
      );
    }

    render(
      <DesignProvider>
        <Gated />
      </DesignProvider>,
    );

    expect(screen.queryByTestId("design-switcher")).toBeNull();
  });
});
