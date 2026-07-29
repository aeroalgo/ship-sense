import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";

import { ThemeSwitcher } from "@/components/ds/ThemeSwitcher";
import {
  readStoredTheme,
  writeStoredTheme,
} from "@/lib/theme/storage";
import {
  DEFAULT_THEME,
  STORAGE_THEME_KEY,
  nextTheme,
  type ThemeId,
} from "@/lib/theme/types";

import { ThemeProvider, useTheme } from "./ThemeProvider";

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

function ThemeProbe() {
  const { theme, setTheme, cycleTheme } = useTheme();
  return (
    <div>
      <span data-testid="theme-value">{theme}</span>
      <ThemeSwitcher theme={theme} onChange={setTheme} />
      <button type="button" data-testid="cycle-theme" onClick={cycleTheme}>
        cycle
      </button>
    </div>
  );
}

describe("theme storage + cycle", () => {
  afterEach(() => {
    cleanup();
  });

  it("defaults to day when storage empty", () => {
    const storage = memoryStorage();
    expect(readStoredTheme(storage)).toBe(DEFAULT_THEME);
    expect(readStoredTheme(storage)).toBe("day");
  });

  it("rejects invalid storage values", () => {
    const storage = memoryStorage({ [STORAGE_THEME_KEY]: "solar" });
    expect(readStoredTheme(storage)).toBe("day");
  });

  it("round-trips theme through storage", () => {
    const storage = memoryStorage();
    writeStoredTheme("night", storage);
    expect(readStoredTheme(storage)).toBe("night");
    writeStoredTheme("dim", storage);
    expect(readStoredTheme(storage)).toBe("dim");
  });

  it("cycles day → night → dim → day", () => {
    expect(nextTheme("day")).toBe("night");
    expect(nextTheme("night")).toBe("dim");
    expect(nextTheme("dim")).toBe("day");
  });
});

describe("ThemeProvider", () => {
  let storage: Storage;

  beforeEach(() => {
    storage = memoryStorage();
    Object.defineProperty(window, "localStorage", {
      configurable: true,
      value: storage,
    });
    document.documentElement.removeAttribute("data-theme");
  });

  afterEach(() => {
    cleanup();
    document.documentElement.removeAttribute("data-theme");
  });

  it("applies stored theme to html and persists switcher changes", () => {
    writeStoredTheme("night", storage);
    render(
      <ThemeProvider>
        <ThemeProbe />
      </ThemeProvider>,
    );

    expect(screen.getByTestId("theme-value").textContent).toBe("night");
    expect(document.documentElement.getAttribute("data-theme")).toBe("night");

    fireEvent.click(screen.getByTestId("theme-switcher"));
    expect(screen.getByTestId("theme-value").textContent).toBe("dim");
    expect(document.documentElement.getAttribute("data-theme")).toBe("dim");
    expect(storage.getItem(STORAGE_THEME_KEY)).toBe("dim");
  });

  it("cycleTheme advances and writes storage", () => {
    render(
      <ThemeProvider>
        <ThemeProbe />
      </ThemeProvider>,
    );

    expect(screen.getByTestId("theme-value").textContent).toBe("day");
    fireEvent.click(screen.getByTestId("cycle-theme"));
    expect(screen.getByTestId("theme-value").textContent).toBe("night");
    expect(storage.getItem(STORAGE_THEME_KEY)).toBe("night");
  });

  it("setTheme ignores invalid values at type boundary via nextTheme only", () => {
    const themes: ThemeId[] = ["day", "night", "dim"];
    let current: ThemeId = "day";
    for (let i = 0; i < 6; i += 1) {
      current = nextTheme(current);
      expect(themes).toContain(current);
    }
  });
});
