export const PUBLIC_ENV_KEYS = [
  "NEXT_PUBLIC_API_URL",
  "NEXT_PUBLIC_WS_URL",
  "NEXT_PUBLIC_STALE_THRESHOLD_SEC",
] as const;

export type PublicEnvKey = (typeof PUBLIC_ENV_KEYS)[number];

export function parseEnvExampleKeys(content: string): string[] {
  const keys: string[] = [];
  for (const line of content.split(/\r?\n/)) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const eq = trimmed.indexOf("=");
    if (eq <= 0) continue;
    keys.push(trimmed.slice(0, eq));
  }
  return keys;
}

export function missingPublicEnvKeys(exampleKeys: string[]): PublicEnvKey[] {
  return PUBLIC_ENV_KEYS.filter((key) => !exampleKeys.includes(key));
}
