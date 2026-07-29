import {
  DEFAULT_DESIGN,
  DEFAULT_THEME,
  STORAGE_DESIGN_KEY,
  STORAGE_THEME_KEY,
  isDesignId,
  isThemeId,
  type DesignId,
  type ThemeId,
} from "./types";

export type StorageLike = Pick<Storage, "getItem" | "setItem" | "removeItem">;

export function readStoredTheme(
  storage: StorageLike | null | undefined,
): ThemeId {
  if (!storage) return DEFAULT_THEME;
  try {
    const value = storage.getItem(STORAGE_THEME_KEY);
    if (value !== null && isThemeId(value)) return value;
  } catch {
    return DEFAULT_THEME;
  }
  return DEFAULT_THEME;
}

export function writeStoredTheme(
  theme: ThemeId,
  storage: StorageLike | null | undefined,
): void {
  if (!storage) return;
  try {
    storage.setItem(STORAGE_THEME_KEY, theme);
  } catch {
    return;
  }
}

export function readStoredDesign(
  storage: StorageLike | null | undefined,
): DesignId {
  if (!storage) return DEFAULT_DESIGN;
  try {
    const value = storage.getItem(STORAGE_DESIGN_KEY);
    if (value !== null && isDesignId(value)) return value;
  } catch {
    return DEFAULT_DESIGN;
  }
  return DEFAULT_DESIGN;
}

export function writeStoredDesign(
  design: DesignId,
  storage: StorageLike | null | undefined,
): void {
  if (!storage) return;
  try {
    storage.setItem(STORAGE_DESIGN_KEY, design);
  } catch {
    return;
  }
}

export function applyThemeAttr(theme: ThemeId, el: HTMLElement): void {
  el.setAttribute("data-theme", theme);
}

export function applyDesignAttr(design: DesignId, el: HTMLElement): void {
  el.setAttribute("data-design", design);
}
