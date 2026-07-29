import type { ChartMode } from "@/lib/trends/chart-lib-spec";

export type TrendsParams = {
  tags: string[];
  from: string | null;
  to: string | null;
  mode: ChartMode;
};

const PRESET_MS = {
  "1h": 60 * 60 * 1000,
  "8h": 8 * 60 * 60 * 1000,
  "24h": 24 * 60 * 60 * 1000,
  "7d": 7 * 24 * 60 * 60 * 1000,
} as const;

export type RangePreset = keyof typeof PRESET_MS;

export function parseTrendsSearchParams(
  params: URLSearchParams,
): TrendsParams {
  const tag = params.get("tag");
  const tagsParam = params.getAll("tags");
  const tags: string[] = [];
  if (tag) tags.push(tag);
  for (const t of tagsParam) {
    if (t && !tags.includes(t)) tags.push(t);
  }

  const modeRaw = params.get("mode");
  const mode: ChartMode =
    modeRaw === "extended" ? "extended" : "quick";

  return {
    tags,
    from: params.get("from"),
    to: params.get("to"),
    mode,
  };
}

export function serializeTrendsParams(state: TrendsParams): URLSearchParams {
  const params = new URLSearchParams();
  if (state.tags[0]) params.set("tag", state.tags[0]);
  for (const t of state.tags.slice(1)) {
    params.append("tags", t);
  }
  if (state.from) params.set("from", state.from);
  if (state.to) params.set("to", state.to);
  params.set("mode", state.mode);
  return params;
}

export function defaultRange(mode: ChartMode): { from: string; to: string } {
  const to = Date.now();
  const span = mode === "quick" ? PRESET_MS["1h"] : PRESET_MS["24h"];
  return {
    from: new Date(to - span).toISOString(),
    to: new Date(to).toISOString(),
  };
}

export function rangeFromPreset(
  preset: RangePreset,
  anchorTo: number = Date.now(),
): { from: string; to: string } {
  return {
    from: new Date(anchorTo - PRESET_MS[preset]).toISOString(),
    to: new Date(anchorTo).toISOString(),
  };
}

export const RANGE_PRESETS: RangePreset[] = ["1h", "8h", "24h", "7d"];
