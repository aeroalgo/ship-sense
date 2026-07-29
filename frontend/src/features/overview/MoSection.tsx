"use client";

import type { ReactNode } from "react";

import { OverviewGroupCard } from "@/components/ds/OverviewGroupCard";
import type { AssetTreeNode } from "@/lib/api/types";

import type { MoSectionId } from "./treeUtils";

export const MO_SECTION_TEST_ID = "mo-section";

export type MoSectionProps = {
  section: MoSectionId;
  title: string;
  groups: AssetTreeNode[];
  onGroupClick: (group: AssetTreeNode) => void;
};

export function MoSection({
  section,
  title,
  groups,
  onGroupClick,
}: MoSectionProps): ReactNode {
  return (
    <section
      data-testid={MO_SECTION_TEST_ID}
      data-section={section}
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "var(--space-3, 12px)",
        minWidth: 0,
      }}
    >
      <h2
        style={{
          margin: 0,
          fontFamily: "var(--font-sans)",
          fontSize: "var(--font-title, 1.25rem)",
          color: "var(--text-primary)",
          fontWeight: 600,
        }}
      >
        {title}
      </h2>
      <div
        style={{
          display: "grid",
          gridTemplateColumns:
            "repeat(auto-fill, minmax(var(--overview-group-min-w, 176px), 1fr))",
          gap: "var(--space-4, 16px)",
        }}
      >
        {groups.map((group) => (
          <OverviewGroupCard
            key={group.id}
            name={group.name}
            status={group.status}
            onClick={() => onGroupClick(group)}
          />
        ))}
      </div>
      {groups.length === 0 ? (
        <p
          style={{
            margin: 0,
            color: "var(--text-muted)",
            fontFamily: "var(--font-sans)",
            fontSize: "var(--font-caption, 0.875rem)",
          }}
        >
          Нет групп
        </p>
      ) : null}
    </section>
  );
}
