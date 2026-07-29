import type {
  AssetsTreeResponse,
  EventsListResponse,
  ReportsListResponse,
  RosterResponse,
  SeriesPoint,
  SeriesResponse,
  SessionResponse,
  SetpointHistoryResponse,
  SetpointsResponse,
  SourcesStatusResponse,
  WatchReportResponse,
} from "@/lib/api/types";
import type { AssetTreeNode } from "@/lib/api/types";
import type { Quality } from "@/lib/quality/types";

function tagLeaf(
  kks: string,
  name: string,
  unit: string,
  value: number | null,
  quality: Quality,
  status: AssetTreeNode["status"] = quality,
): AssetTreeNode {
  return {
    id: `tag_${kks}`,
    kind: "tag",
    tag_id: kks,
    name: `${kks} ${name}`,
    unit,
    status,
    last_value: value,
    last_quality: quality,
  };
}

function buildOilTempSeries(): SeriesPoint[] {
  const points: SeriesPoint[] = [];
  const start = Date.parse("2026-07-26T08:00:00Z");
  for (let i = 0; i < 48; i += 1) {
    const ts = new Date(start + i * 10 * 60_000).toISOString().replace(".000Z", "Z");
    if (i === 12) {
      points.push({
        ts,
        value: null,
        quality: "bad",
        min: null,
        max: null,
        samples: 0,
      });
      continue;
    }
    const base = 52 + Math.sin(i / 5) * 3.5 + (i > 30 ? (i - 30) * 0.35 : 0);
    const value = Math.round(base * 10) / 10;
    points.push({
      ts,
      value,
      quality: i > 36 ? "uncertain" : "good",
      min: Math.round((value - 0.4) * 10) / 10,
      max: Math.round((value + 0.6) * 10) / 10,
      samples: 60,
    });
  }
  return points;
}

export const assetsTreeFixture: AssetsTreeResponse = {
  root: {
    id: "ship",
    kind: "plant",
    name: "Ледокол Адмирал Макаров",
    status: "uncertain",
    worst_tag_id: "TAI4101",
    children: [
      {
        id: "mo_nos",
        kind: "system",
        name: "НДО — носовое дизельное отделение",
        status: "good",
        worst_tag_id: null,
        children: [
          {
            id: "sys_geu_1",
            kind: "system",
            name: "ГЭУ №1 (ГД1)",
            status: "uncertain",
            worst_tag_id: "TAI4101",
            children: [
              {
                id: "eq_gd1_cylinders",
                kind: "equipment",
                name: "Цилиндры ГД1",
                status: "good",
                worst_tag_id: null,
                children: [
                  tagLeaf("TAI1101", "t° выхлопа цил.1 канал а", "°C", 412.0, "good"),
                  tagLeaf("TAI1103", "t° выхлопа цил.2 канал а", "°C", 408.5, "good"),
                ],
              },
              {
                id: "eq_gd1_lube",
                kind: "equipment",
                name: "Система смазки ГД1",
                status: "uncertain",
                worst_tag_id: "TAI4101",
                children: [
                  tagLeaf("TAI4101", "t° смазочного масла", "°C", 61.8, "uncertain"),
                  tagLeaf("LA1611", "низкий уровень смазки цилиндров", "-", 0, "good"),
                ],
              },
              {
                id: "eq_gd1_cooling",
                kind: "equipment",
                name: "Охлаждение ГД1",
                status: "good",
                worst_tag_id: null,
                children: [
                  tagLeaf("TAI5101", "t° пресной охлаждающей воды", "°C", 68.2, "good"),
                  tagLeaf("TAI5111", "t° воды охлаждения форсунок", "°C", 54.1, "good"),
                  tagLeaf("XA5173", "помеха насоса охлаждения форсунок", "-", 0, "good"),
                ],
              },
            ],
          },
          {
            id: "sys_vdg_1",
            kind: "system",
            name: "ВДГ №1",
            status: "good",
            worst_tag_id: null,
            children: [
              {
                id: "eq_vd1",
                kind: "equipment",
                name: "Вспомогательный ДГ №1",
                status: "good",
                worst_tag_id: null,
                children: [
                  tagLeaf("TAI2301", "t° выхлопных газов", "°C", 355.0, "good"),
                  tagLeaf("TA4111", "t° смазочного масла", "°C", 58.4, "good"),
                  tagLeaf("PA4131", "давление смазочного масла", "-", 1, "good"),
                ],
              },
            ],
          },
          {
            id: "sys_ndo_aux",
            kind: "system",
            name: "Вспомогательные НДО",
            status: "good",
            worst_tag_id: null,
            children: [
              {
                id: "eq_ndo_bilge",
                kind: "equipment",
                name: "Льяльные воды / воздух НДО",
                status: "good",
                worst_tag_id: null,
                children: [
                  tagLeaf("LA6111", "высокий уровень льяльных вод НДО", "-", 0, "good"),
                  tagLeaf("PA7151", "давление воздуха в НДО", "-", 1, "good"),
                  tagLeaf("15A102", "t° воздуха в НДО", "°C", 24.6, "good"),
                ],
              },
            ],
          },
        ],
      },
      {
        id: "mo_stern",
        kind: "system",
        name: "КДО — кормовое дизельное отделение",
        status: "uncertain",
        worst_tag_id: "15A57",
        children: [
          {
            id: "sys_geu_5",
            kind: "system",
            name: "ГЭУ №5–6 (ГД5–6)",
            status: "stale",
            worst_tag_id: "PAI3113",
            children: [
              {
                id: "eq_gd5_fuel",
                kind: "equipment",
                name: "Топливная система ГД5–6",
                status: "stale",
                worst_tag_id: "PAI3113",
                children: [
                  tagLeaf("PAI3113", "давление топлива на входе ГД5–6", "кг/см²", 4.2, "stale", "stale"),
                  tagLeaf("XA3413", "помеха ТПН ГД5–6", "-", 0, "good"),
                ],
              },
            ],
          },
          {
            id: "sys_skt_ged",
            kind: "system",
            name: "СКТ ГЭУ — гребной электродвигатель",
            status: "uncertain",
            worst_tag_id: "15A57",
            children: [
              {
                id: "eq_ged1",
                kind: "equipment",
                name: "ГЭД №1",
                status: "uncertain",
                worst_tag_id: "15A57",
                children: [
                  tagLeaf("15A47", "выходящий воздух ГЭД", "°C", 72.0, "good"),
                  tagLeaf("15A49", "главный полюс ГЭД", "°C", 81.5, "good"),
                  tagLeaf("15A57", "охлаждающая вода ГЭД", "°C", 48.0, "uncertain"),
                ],
              },
            ],
          },
          {
            id: "sys_protection",
            kind: "system",
            name: "Защиты / аварийные остановы",
            status: "good",
            worst_tag_id: null,
            children: [
              {
                id: "eq_shutdown_gd",
                kind: "equipment",
                name: "Аварийные остановы ГЭУ",
                status: "good",
                worst_tag_id: null,
                children: [
                  tagLeaf("14D34", "АО: низкое давление масла", "-", 0, "good"),
                  tagLeaf("14D39", "АО: сверхобороты", "-", 0, "good"),
                  tagLeaf("14D44", "АО: высокая температура", "-", 0, "good"),
                ],
              },
            ],
          },
          {
            id: "sys_kdo_aux",
            kind: "system",
            name: "Вспомогательные КДО",
            status: "good",
            worst_tag_id: null,
            children: [
              {
                id: "eq_kdo_bilge",
                kind: "equipment",
                name: "Льяльные воды / воздух КДО",
                status: "good",
                worst_tag_id: null,
                children: [
                  tagLeaf("LA6112", "высокий уровень льяльных вод КДО", "-", 0, "good"),
                  tagLeaf("PA7152", "давление воздуха в КДО", "-", 1, "good"),
                  tagLeaf("15A103", "t° воздуха в КДО", "°C", 26.1, "good"),
                  tagLeaf("TAI3521", "t° вспомогательных паровых котлов", "°C", 142.0, "good"),
                ],
              },
            ],
          },
        ],
      },
    ],
  },
  generated_at: "2026-07-26T14:00:00Z",
};

export const eventsListFixture: EventsListResponse = {
  items: [
    {
      id: "evt_00001234",
      ts: "2026-07-26T07:58:12Z",
      event_name: "alarm.HH",
      severity: "alarm",
      source: "aps",
      asset_id: "eq_gd1_lube",
      params: {
        kks: "TAI4101",
        threshold: 65.0,
        value: 66.4,
        system: "ГЭУ1",
        reconstructed: false,
      },
      quality: null,
    },
    {
      id: "evt_00001235",
      ts: "2026-07-26T08:00:01Z",
      event_name: "session_started",
      severity: "info",
      source: "edge",
      asset_id: null,
      params: {
        session_id: "sess_uuid",
        person_id: "ivanov",
        name: "Иванов И.И.",
      },
      quality: null,
    },
    {
      id: "evt_00001236",
      ts: "2026-07-26T08:05:44Z",
      event_name: "protection.trip",
      severity: "alarm",
      source: "aps",
      asset_id: "eq_shutdown_gd",
      params: {
        kks: "14D39",
        system: "ГЭУ1",
        label: "АО: сверхобороты",
      },
      quality: null,
    },
    {
      id: "evt_00001237",
      ts: "2026-07-26T09:12:03Z",
      event_name: "alarm.LL",
      severity: "warning",
      source: "aps",
      asset_id: "eq_gd1_lube",
      params: {
        kks: "LA1611",
        system: "ГЭУ1",
        label: "Низкий уровень смазки цилиндров",
      },
      quality: null,
    },
    {
      id: "evt_00001238",
      ts: "2026-07-26T10:41:22Z",
      event_name: "alarm.warning",
      severity: "warning",
      source: "aps",
      asset_id: "eq_gd5_fuel",
      params: {
        kks: "XA3413",
        system: "ГЭУ5-6",
        label: "Помеха ТПН ГД5–6",
      },
      quality: null,
    },
    {
      id: "evt_00001239",
      ts: "2026-07-26T11:05:10Z",
      event_name: "alarm.HH",
      severity: "alarm",
      source: "skt_geu",
      asset_id: "eq_ged1",
      params: {
        kks: "15A49",
        threshold: 90.0,
        value: 92.3,
        system: "ГЭД1",
        label: "Главный полюс ГЭД",
      },
      quality: null,
    },
  ],
  next_cursor:
    "eyJ0cyI6IjIwMjYtMDctMjZUMTE6MDU6MTBaIiwiaWQiOiJldnRfMDAwMDEyMzkifQ",
  has_more: true,
};

export const seriesFixture: SeriesResponse = {
  tag_id: "TAI4101",
  name: "TAI4101 t° смазочного масла ГД1",
  unit: "°C",
  from: "2026-07-26T08:00:00Z",
  to: "2026-07-26T16:00:00Z",
  resolution: "10m",
  points: buildOilTempSeries(),
};

export const setpointsFixture: SetpointsResponse = {
  items: [
    {
      tag_id: "sp_TAI4101_HH",
      value: 65.0,
      unit: "°C",
      label: "HH TAI4101 смазка ГД1",
      effective_from: "2026-01-15T00:00:00Z",
    },
    {
      tag_id: "sp_TAI1101_HH",
      value: 520.0,
      unit: "°C",
      label: "HH TAI1101 выхлоп цил.1",
      effective_from: "2026-01-15T00:00:00Z",
    },
  ],
};

export const setpointHistoryFixture: SetpointHistoryResponse = {
  tag_id: "sp_TAI4101_HH",
  segments: [
    {
      from_ts: "2026-01-01T00:00:00Z",
      to_ts: "2026-01-15T00:00:00Z",
      value: 62.0,
    },
    {
      from_ts: "2026-01-15T00:00:00Z",
      to_ts: null,
      value: 65.0,
    },
  ],
};

export const reportsListFixture: ReportsListResponse = {
  items: [
    {
      type: "watch",
      title: "Вахтенная сводка",
      formats: ["json", "html"],
      description: "Сводка вахты по АПС + СКТ ГЭУ (прототип экрана 6)",
    },
  ],
};

export const watchReportFixture: WatchReportResponse = {
  generated_at: "2026-07-26T16:00:00Z",
  watchkeeper: {
    person_id: "ivanov",
    name: "Иванов И.И.",
    rank: "вахтенный механик",
  },
  period: {
    from: "2026-07-26T08:00:00Z",
    to: "2026-07-26T16:00:00Z",
  },
  data_quality: {
    quarantine_tags: ["unknown_native_40099"],
    stale_intervals: [
      { from: "2026-07-26T10:00:00Z", to: "2026-07-26T10:05:00Z" },
    ],
    banner: "Часть периода под сверкой: см. quarantine_tags",
  },
  summary: {
    events_count: 42,
    alarms_count: 3,
    protections_count: 1,
    verdict: "Были тревоги по ГЭУ1 (смазка); защит 1 (сверхобороты)",
  },
  highlights: [],
  tags_snapshot: [
    {
      tag_id: "TAI4101",
      name: "TAI4101",
      avg: 56.4,
      min: 48.2,
      max: 66.4,
      quality_worst: "uncertain",
    },
    {
      tag_id: "TAI1101",
      name: "TAI1101",
      avg: 405.0,
      min: 388.0,
      max: 428.0,
      quality_worst: "good",
    },
    {
      tag_id: "15A49",
      name: "15A49",
      avg: 78.2,
      min: 70.0,
      max: 92.3,
      quality_worst: "good",
    },
  ],
};

export const rosterFixture: RosterResponse = {
  items: [
    {
      person_id: "ivanov",
      name: "Иванов И.И.",
      rank: "вахтенный механик",
      tile_order: 1,
      active: true,
      default_screen: 1,
    },
    {
      person_id: "petrov",
      name: "Петров П.П.",
      rank: "старший механик",
      tile_order: 2,
      active: true,
      default_screen: 6,
    },
    {
      person_id: "sidorov",
      name: "Сидоров С.С.",
      rank: "вахтенный электромеханик",
      tile_order: 3,
      active: true,
      default_screen: 1,
    },
    {
      person_id: "kozlov",
      name: "Козлов А.А.",
      rank: "ст. электромеханик",
      tile_order: 4,
      active: true,
      default_screen: 1,
    },
  ],
};

export const sessionFixture: SessionResponse = {
  session_id: "550e8400-e29b-41d4-a716-446655440000",
  person_id: "ivanov",
  name: "Иванов И.И.",
  rank: "вахтенный механик",
  started_at: "2026-07-26T16:00:00Z",
  expires_at: "2026-07-27T00:00:00Z",
  token: "opaque-uuid-for-bearer-if-needed",
  default_screen: 1,
};

export const sourcesStatusFixture: SourcesStatusResponse = {
  items: [
    {
      source_id: "aps",
      name: "АПС (Fastwel CPM723)",
      connected: true,
      last_poll_ts: "2026-07-26T16:00:00.100Z",
      error_count_24h: 0,
      quality_summary: "good",
      tags_active: 482,
      tags_quarantine: 2,
      tags_stale: 5,
    },
    {
      source_id: "geu_skt",
      name: "СКТ ГЭУ (15A1–15A104)",
      connected: true,
      last_poll_ts: "2026-07-26T16:00:00.105Z",
      error_count_24h: 1,
      quality_summary: "uncertain",
      tags_active: 104,
      tags_quarantine: 0,
      tags_stale: 0,
    },
  ],
};
