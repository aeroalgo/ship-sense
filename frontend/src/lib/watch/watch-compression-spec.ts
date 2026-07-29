export const WATCH_VERDICT_TEST_ID = "watch-verdict";
export const WATCH_SECTION_TEST_ID = "watch-section";
export const DEBOUNCE_GROUP_TEST_ID = "debounce-group-row";
export const DATA_QUALITY_PANEL_TEST_ID = "watch-data-quality";

export const DEBOUNCE_MIN_COUNT = 3;

export const DEBOUNCE_WINDOW_MS = 5 * 60 * 1000;

export const DEBOUNCE_GROUP_KEY_SEP = "\u0001";

export type WatchSectionId = "protections" | "alarms" | "drifts";

export type WatchVerdictTone = "ok" | "attention" | "critical";

export type DebounceEventLike = {
  id: string;
  ts: string;
  event_name: string;
  asset_id: string | null;
  severity?: string | null;
  source?: string | null;
  params?: Record<string, unknown>;
};

export type DebounceGroup = {
  key: string;
  event_name: string;
  asset_id: string | null;
  count: number;
  first_ts: string;
  last_ts: string;
  member_ids: string[];
  collapsed: boolean;
};

export type VerdictInput = {
  alarms_count: number;
  protections_count: number;
  system_labels: string[];
  events_count?: number;
};

export type VerdictResult = {
  text: string;
  tone: WatchVerdictTone;
};

export const PROTECTION_NAME_RE =
  /trip|shutdown|protection|overspeed|разнос|защита|шатдаун|отключ/i;

export function debounceGroupKey(
  event_name: string,
  asset_id: string | null,
): string {
  return `${event_name}${DEBOUNCE_GROUP_KEY_SEP}${asset_id ?? ""}`;
}

export function isProtectionEvent(event: DebounceEventLike): boolean {
  if (event.params?.kind === "protection" || event.params?.section === "protections") {
    return true;
  }
  if (event.severity === "critical" || event.severity === "protection-shutdown") {
    return true;
  }
  return PROTECTION_NAME_RE.test(event.event_name);
}

export function collapseDebounceGroups(
  events: readonly DebounceEventLike[],
  options?: {
    minCount?: number;
    windowMs?: number;
  },
): DebounceGroup[] {
  const minCount = options?.minCount ?? DEBOUNCE_MIN_COUNT;
  const windowMs = options?.windowMs ?? DEBOUNCE_WINDOW_MS;

  const sorted = [...events].sort(
    (a, b) => new Date(a.ts).getTime() - new Date(b.ts).getTime(),
  );

  const byKey = new Map<string, DebounceEventLike[]>();
  for (const event of sorted) {
    const key = debounceGroupKey(event.event_name, event.asset_id);
    const bucket = byKey.get(key);
    if (bucket) {
      bucket.push(event);
    } else {
      byKey.set(key, [event]);
    }
  }

  const groups: DebounceGroup[] = [];

  for (const [key, members] of byKey) {
    let clusterStart = 0;
    while (clusterStart < members.length) {
      const startTs = new Date(members[clusterStart].ts).getTime();
      let clusterEnd = clusterStart + 1;
      while (clusterEnd < members.length) {
        const ts = new Date(members[clusterEnd].ts).getTime();
        if (ts - startTs > windowMs) {
          break;
        }
        clusterEnd += 1;
      }

      const cluster = members.slice(clusterStart, clusterEnd);
      const first = cluster[0];
      const last = cluster[cluster.length - 1];
      const count = cluster.length;
      groups.push({
        key: `${key}${DEBOUNCE_GROUP_KEY_SEP}${first.ts}`,
        event_name: first.event_name,
        asset_id: first.asset_id,
        count,
        first_ts: first.ts,
        last_ts: last.ts,
        member_ids: cluster.map((m) => m.id),
        collapsed: count >= minCount,
      });
      clusterStart = clusterEnd;
    }
  }

  return groups.sort(
    (a, b) => new Date(a.first_ts).getTime() - new Date(b.first_ts).getTime(),
  );
}

export function formatDebounceLabel(
  group: Pick<DebounceGroup, "event_name" | "count" | "collapsed">,
  assetLabel?: string | null,
): string {
  const base = assetLabel
    ? `${assetLabel} - ${group.event_name}`
    : group.event_name;
  if (!group.collapsed) {
    return base;
  }
  return `${base} (×${group.count} дребезг)`;
}

export function buildVerdict(input: VerdictInput): VerdictResult {
  const { alarms_count, protections_count, system_labels } = input;
  const events_count = input.events_count ?? alarms_count + protections_count;

  if (events_count === 0 && alarms_count === 0 && protections_count === 0) {
    return {
      text: "За вахту событий не зафиксировано",
      tone: "ok",
    };
  }

  const systems =
    system_labels.length > 0 ? system_labels.join(", ") : "системам";

  if (protections_count > 0 && alarms_count > 0) {
    return {
      text: `Были тревоги по ${systems}; защит: ${protections_count}`,
      tone: "critical",
    };
  }

  if (protections_count > 0) {
    return {
      text: `Сработали защиты: ${protections_count}`,
      tone: "critical",
    };
  }

  if (alarms_count > 0) {
    return {
      text: `Были тревоги по ${systems}; защит: 0`,
      tone: "attention",
    };
  }

  return {
    text: "За вахту событий не зафиксировано",
    tone: "ok",
  };
}

export function resolveVerdict(args: {
  serverVerdict?: string | null;
  input: VerdictInput;
}): VerdictResult {
  const client = buildVerdict(args.input);
  const server = args.serverVerdict?.trim();
  if (!server) {
    return client;
  }
  return {
    text: server,
    tone: client.tone,
  };
}

export const SECTION_ORDER: readonly WatchSectionId[] = [
  "protections",
  "alarms",
  "drifts",
] as const;

export const SECTION_TITLES: Record<WatchSectionId, string> = {
  protections: "Защиты / шатдауны",
  alarms: "Тревоги по системам",
  drifts: "Дрейфы",
};

export const DRIFTS_STUB_COPY = "Дрейфы параметров: фаза 2 (B13)";

export const HANDOFF_BANNER_MS = 60_000;

export const HANDOFF_BANNER_COPY = "Пересменочный обзор";

export const HANDOFF_PRIMARY = {
  label: "К активным тревогам",
  href: "/journal?severity=alarm&active=1",
} as const;

export const HANDOFF_SECONDARY = {
  label: "Обзор судна",
  href: "/overview",
} as const;
