"use client";

import { useState } from "react";

import {
  DEBOUNCE_GROUP_TEST_ID,
  formatDebounceLabel,
  formatWatchTime,
  type DebounceGroup,
} from "./debounce";

export type DebounceGroupRowProps = {
  group: DebounceGroup;
  assetLabel?: string | null;
  memberTimestamps?: Record<string, string>;
};

export function DebounceGroupRow({
  group,
  assetLabel,
  memberTimestamps,
}: DebounceGroupRowProps) {
  const [expanded, setExpanded] = useState(false);
  const label = formatDebounceLabel(group, assetLabel);
  const time = formatWatchTime(group.first_ts);
  const canExpand = group.collapsed || group.member_ids.length > 1;

  return (
    <li
      data-testid={DEBOUNCE_GROUP_TEST_ID}
      data-collapsed={group.collapsed ? "true" : "false"}
      data-count={String(group.count)}
      style={{
        listStyle: "none",
        minHeight: "var(--touch-min, 48px)",
        padding: "8px 0",
        borderTop: "var(--border-width, 1px) solid var(--border-subtle)",
        color: "var(--text-primary)",
        fontFamily: "var(--font-mono, var(--font-sans))",
        fontSize: "var(--font-body)",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 12,
          justifyContent: "space-between",
        }}
      >
        <span>
          <time dateTime={group.first_ts} style={{ color: "var(--text-secondary)" }}>
            {time}
          </time>
          {" - "}
          {label}
        </span>
        {canExpand ? (
          <button
            type="button"
            aria-expanded={expanded}
            onClick={() => setExpanded((v) => !v)}
            style={{
              minHeight: "var(--touch-min, 48px)",
              minWidth: "var(--touch-min, 48px)",
              padding: "0 12px",
              border: "var(--border-width, 1px) solid var(--border-subtle)",
              background: "var(--surface-0)",
              color: "var(--text-primary)",
              fontFamily: "inherit",
              fontSize: "var(--font-caption, 0.875rem)",
              cursor: "pointer",
            }}
          >
            {expanded ? "свернуть" : "развернуть"}
          </button>
        ) : null}
      </div>
      {expanded ? (
        <ul
          style={{
            listStyle: "none",
            margin: "8px 0 0",
            padding: 0,
            color: "var(--text-secondary)",
            fontSize: "var(--font-caption, 0.875rem)",
          }}
        >
          {group.member_ids.map((id) => {
            const ts = memberTimestamps?.[id] ?? id;
            return (
              <li key={id} style={{ padding: "4px 0" }}>
                <time dateTime={memberTimestamps?.[id] ?? undefined}>
                  {memberTimestamps?.[id]
                    ? formatWatchTime(memberTimestamps[id])
                    : ts}
                </time>
                {" · "}
                {id}
              </li>
            );
          })}
        </ul>
      ) : null}
      {group.collapsed && !expanded ? (
        <p
          style={{
            margin: "4px 0 0",
            color: "var(--text-muted)",
            fontSize: "var(--font-caption, 0.875rem)",
          }}
        >
          {group.count} срабатываний; детали в журнале
        </p>
      ) : null}
    </li>
  );
}
