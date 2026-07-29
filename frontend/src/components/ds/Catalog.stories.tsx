import type { Meta, StoryObj } from "@storybook/react";

import type { EventItem } from "@/lib/api/types";

import { AggregateShipStatus } from "./AggregateShipStatus";
import { EventFilters } from "./EventFilters";
import { EventRow } from "./EventRow";
import { FreshnessBanner } from "./FreshnessBanner";
import { LoginTile } from "./LoginTile";
import { OverviewGroupCard } from "./OverviewGroupCard";
import { PrintLayout } from "./PrintLayout";
import { QuarantineBanner } from "./QuarantineBanner";
import { SessionChip } from "./SessionChip";
import { SelectedTags, TagPicker } from "./TagPicker";
import { WatchSection } from "./WatchSection";
import { WatchVerdict } from "./WatchVerdict";

const sampleEvent: EventItem = {
  id: "e1",
  ts: "2026-07-26T07:58:12Z",
  event_name: "HH TAI4101",
  severity: "alarm",
  source: "aps",
  asset_id: "geu1",
  params: {},
  quality: "good",
};

const meta: Meta = {
  title: "DS/Catalog",
};

export default meta;

type Story = StoryObj;

export const AggregateShipStatusStates: Story = {
  name: "AggregateShipStatus — loading/empty/error/partial/stale",
  render: () => (
    <div style={{ display: "grid", gap: 12 }}>
      <AggregateShipStatus status="unknown" label="Загрузка статуса…" />
      <AggregateShipStatus status="good" label="Судно в норме" />
      <AggregateShipStatus
        status="bad"
        label="Ошибка качества"
        worstSeverity="alarm"
      />
      <AggregateShipStatus
        status="quarantine"
        label="Частичные данные"
        worstSeverity="alarm"
      />
      <AggregateShipStatus
        status="stale"
        label="Устарело"
        worstSeverity="warning-drift"
      />
    </div>
  ),
};

export const OverviewGroupCardStates: Story = {
  name: "OverviewGroupCard — loading/empty/error/partial/stale",
  render: () => (
    <div style={{ display: "flex", flexWrap: "wrap", gap: 12 }}>
      <OverviewGroupCard name="…" status="unknown" />
      <OverviewGroupCard name="ГЭУ1" status="good" />
      <OverviewGroupCard name="Насосы" status="bad" />
      <OverviewGroupCard
        name="СЭС"
        status="quarantine"
        alarmCount={2}
        worstSeverity="alarm"
      />
      <OverviewGroupCard name="Вентиляция" status="stale" alarmCount={1} />
    </div>
  ),
};

export const EventRowStates: Story = {
  name: "EventRow — loading/empty/error/partial/stale",
  render: () => (
    <div>
      <EventRow
        event={{
          ...sampleEvent,
          id: "load",
          event_name: "Загрузка…",
          severity: null,
          quality: null,
        }}
      />
      <EventRow
        event={{
          ...sampleEvent,
          id: "empty",
          event_name: "Нет событий",
          severity: "info",
        }}
      />
      <EventRow
        event={{
          ...sampleEvent,
          id: "err",
          severity: "alarm",
          quality: "bad",
        }}
      />
      <EventRow
        event={{
          ...sampleEvent,
          id: "part",
          severity: "warning",
          quality: "quarantine",
        }}
      />
      <EventRow
        event={{
          ...sampleEvent,
          id: "stale",
          severity: "alarm",
          quality: "stale",
        }}
      />
    </div>
  ),
};

export const EventFiltersStates: Story = {
  name: "EventFilters — loading/empty/error/partial/stale",
  render: () => (
    <div style={{ display: "grid", gap: 12 }}>
      <EventFilters filters={{}} onChange={() => undefined} />
      <EventFilters
        filters={{ severity: "" }}
        onChange={() => undefined}
      />
      <EventFilters
        filters={{ severity: "alarm", eventName: "ошибка канала" }}
        onChange={() => undefined}
      />
      <EventFilters
        filters={{ severity: "warning", assetId: "geu1" }}
        onChange={() => undefined}
        onPrint={() => undefined}
      />
      <EventFilters
        filters={{ from: "2026-07-26T00:00", to: "2026-07-26T08:00" }}
        onChange={() => undefined}
      />
    </div>
  ),
};

export const TagPickerStates: Story = {
  name: "TagPicker — loading/empty/error/partial/stale",
  render: () => (
    <div style={{ display: "grid", gap: 12 }}>
      <TagPicker tags={[]} selected={[]} onAdd={() => undefined} />
      <TagPicker
        tags={[{ id: "t1", name: "TAI4101" }]}
        selected={[]}
        onAdd={() => undefined}
      />
      <div>
        <TagPicker
          tags={[{ id: "t1", name: "TAI4101" }]}
          selected={["missing"]}
          onAdd={() => undefined}
        />
        <SelectedTags
          tags={[{ id: "t1", name: "TAI4101" }]}
          selected={["missing"]}
          onRemove={() => undefined}
        />
      </div>
      <div>
        <TagPicker
          tags={[
            { id: "t1", name: "TAI4101" },
            { id: "t2", name: "TAI4102" },
          ]}
          selected={["t1"]}
          onAdd={() => undefined}
        />
        <SelectedTags
          tags={[
            { id: "t1", name: "TAI4101" },
            { id: "t2", name: "TAI4102" },
          ]}
          selected={["t1"]}
          onRemove={() => undefined}
        />
      </div>
      <div>
        <TagPicker
          tags={[{ id: "t1", name: "TAI4101 (stale)" }]}
          selected={["t1"]}
          onAdd={() => undefined}
        />
        <SelectedTags
          tags={[{ id: "t1", name: "TAI4101 (stale)" }]}
          selected={["t1"]}
          onRemove={() => undefined}
        />
      </div>
    </div>
  ),
};

export const WatchVerdictStates: Story = {
  name: "WatchVerdict — loading/empty/error/partial/stale",
  render: () => (
    <div style={{ display: "grid", gap: 8 }}>
      <WatchVerdict text="Формирование сводки…" tone="ok" />
      <WatchVerdict text="Нет сводки" tone="ok" />
      <WatchVerdict text="Ошибка расчёта вахты" tone="critical" />
      <WatchVerdict text="Часть тегов под сверкой" tone="attention" />
      <WatchVerdict text="Данные устарели" tone="attention" />
    </div>
  ),
};

export const WatchSectionStates: Story = {
  name: "WatchSection — loading/empty/error/partial/stale",
  render: () => (
    <div style={{ display: "grid", gap: 12 }}>
      <WatchSection title="Загрузка" items={[]} />
      <WatchSection title="Пусто" items={[]} collapsible />
      <WatchSection
        title="Ошибка"
        items={[{ id: "1", label: "Канал недоступен", detail: "error" }]}
      />
      <WatchSection
        title="Частично"
        items={[
          { id: "1", label: "СЭС", detail: "quarantine" },
          { id: "2", label: "Насосы", detail: "uncertain" },
        ]}
      />
      <WatchSection
        title="Устарело"
        items={[{ id: "1", label: "Последний снимок", detail: "stale" }]}
        collapsible
        defaultOpen={false}
      />
    </div>
  ),
};

export const LoginTileStates: Story = {
  name: "LoginTile — loading/empty/error/partial/stale",
  render: () => (
    <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
      <LoginTile person="…" personId="loading" rank="-" />
      <LoginTile person="Иванов" personId="ivanov" rank="вахтенный" />
      <LoginTile person="Ошибка" personId="err" rank="нет связи" />
      <LoginTile
        person="Петров"
        personId="petrov"
        rank="старший"
        active
      />
      <LoginTile person="Сидоров" personId="sid" rank="вахтенный (устарело)" />
    </div>
  ),
};

export const BannerStates: Story = {
  name: "Banners — loading/empty/error/partial/stale",
  render: () => (
    <div style={{ display: "grid", gap: 8 }}>
      <FreshnessBanner lastTs={null} stale={false} message="Загрузка…" />
      <FreshnessBanner lastTs={null} stale={false} />
      <FreshnessBanner
        lastTs={null}
        stale
        message="Ошибка связи с edge"
      />
      <QuarantineBanner tags={["t1", "t2"]} scope="обзор" />
      <FreshnessBanner lastTs="2026-07-26T07:50:00Z" stale />
    </div>
  ),
};

export const PrintAndSession: Story = {
  name: "PrintLayout / SessionChip — loading/empty/error/partial/stale",
  render: () => (
    <div style={{ display: "grid", gap: 12 }}>
      <SessionChip name="…" rank="-" />
      <SessionChip name="Иванов" rank="вахтенный" onLogout={() => undefined} />
      <PrintLayout title="Ошибка печати" provenance="источник недоступен">
        <p style={{ margin: 0 }}>Нет данных</p>
      </PrintLayout>
      <PrintLayout title="Частичный отчёт" provenance="карантин: 2 тега">
        <p style={{ margin: 0 }}>Часть строк скрыта</p>
      </PrintLayout>
      <PrintLayout title="Устаревший снимок" provenance="ts: 07:50">
        <p style={{ margin: 0 }}>Содержимое для печати</p>
      </PrintLayout>
    </div>
  ),
};
