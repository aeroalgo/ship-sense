import type { AssetTreeNode, AssetsTreeResponse } from "@/lib/api/types";
import { rollupNode } from "@/lib/quality/rollup";
import type { AggregateStatus, Quality } from "@/lib/quality/types";
import { WS_MAX_TAGS } from "@/lib/ws/types";

export type MoSectionId = "nos" | "stern";

export const SHIP_STATUS_COPY: Record<AggregateStatus, string> = {
  good: "НОРМА",
  uncertain: "ВНИМАНИЕ",
  bad: "НЕИСПРАВНОСТЬ",
  stale: "УСТАРЕЛО",
  quarantine: "СВЕРКА",
  unknown: "НЕТ ДАННЫХ",
};

export function shipStatusLabel(status: AggregateStatus): string {
  return `Судно: ${SHIP_STATUS_COPY[status]}`;
}

export function flattenTagIds(
  root: AssetTreeNode,
  max: number = WS_MAX_TAGS,
): string[] {
  const ids: string[] = [];

  function walk(node: AssetTreeNode): void {
    if (ids.length >= max) return;
    if (node.kind === "tag" && node.tag_id) {
      ids.push(node.tag_id);
      return;
    }
    for (const child of node.children ?? []) {
      walk(child);
      if (ids.length >= max) return;
    }
  }

  walk(root);
  return ids;
}

export function collectQuarantineTagIds(root: AssetTreeNode): string[] {
  const ids: string[] = [];

  function walk(node: AssetTreeNode): void {
    if (node.kind === "tag") {
      if (
        (node.last_quality === "quarantine" || node.status === "quarantine") &&
        node.tag_id
      ) {
        ids.push(node.tag_id);
      }
      return;
    }
    for (const child of node.children ?? []) {
      walk(child);
    }
  }

  walk(root);
  return ids;
}

export function rollupTree(node: AssetTreeNode): AssetTreeNode {
  if (node.kind === "tag" || !node.children?.length) {
    const leafStatus: AggregateStatus =
      node.kind === "tag"
        ? ((node.last_quality ?? node.status) as AggregateStatus)
        : node.status;
    return { ...node, status: leafStatus, children: node.children };
  }

  const children = node.children.map(rollupTree);
  return {
    ...node,
    children,
    status: rollupNode(children.map((child) => child.status)),
  };
}

export function applyValueToTree(
  root: AssetTreeNode,
  tagId: string,
  value: number | null,
  quality: Quality,
): AssetTreeNode {
  function walk(node: AssetTreeNode): AssetTreeNode {
    if (node.kind === "tag" && node.tag_id === tagId) {
      return {
        ...node,
        last_value: value,
        last_quality: quality,
        status: quality,
      };
    }
    if (!node.children?.length) return node;
    return { ...node, children: node.children.map(walk) };
  }

  return rollupTree(walk(root));
}

function resolveMoSection(node: AssetTreeNode): MoSectionId {
  const key = `${node.id} ${node.name}`.toLowerCase();
  if (/stern|корма|aft/.test(key)) return "stern";
  if (/nos|bow|нос|fore/.test(key)) return "nos";
  if (/propulsion|движит|geu|гэд|гд\b|главн/.test(key)) return "stern";
  return "nos";
}

export function systemGroups(root: AssetTreeNode): AssetTreeNode[] {
  const children = root.children ?? [];
  if (children.length === 0) return [];

  const moContainers = children.filter((child) => {
    const key = `${child.id}`.toLowerCase();
    return key === "mo_nos" || key === "mo_stern" || key === "nos" || key === "stern";
  });

  if (moContainers.length > 0) {
    return moContainers.flatMap((section) =>
      (section.children ?? []).filter(
        (child) => child.kind === "system" || child.kind === "equipment",
      ),
    );
  }

  return children.filter(
    (child) => child.kind === "system" || child.kind === "equipment",
  );
}

export function partitionMoSections(root: AssetTreeNode): Record<
  MoSectionId,
  AssetTreeNode[]
> {
  const groups = systemGroups(root);
  const result: Record<MoSectionId, AssetTreeNode[]> = { nos: [], stern: [] };
  for (const group of groups) {
    result[resolveMoSection(group)].push(group);
  }
  return result;
}

export function hasOverviewData(tree: AssetsTreeResponse): boolean {
  return systemGroups(tree.root).length > 0;
}
