import type { AggregateStatus, Quality } from "./types";

const WORST_RANK: Record<Quality, number> = {
  good: 1,
  uncertain: 2,
  bad: 3,
  stale: 4,
  quarantine: 5,
};

export function worstOf(qualities: readonly Quality[]): AggregateStatus {
  if (qualities.length === 0) {
    return "unknown";
  }

  let worst: Quality = qualities[0];
  let worstRank = WORST_RANK[worst];

  for (let i = 1; i < qualities.length; i += 1) {
    const quality = qualities[i];
    const rank = WORST_RANK[quality];
    if (rank > worstRank) {
      worst = quality;
      worstRank = rank;
    }
  }

  return worst;
}

export function rollupNode(
  childrenStatuses: readonly AggregateStatus[],
): AggregateStatus {
  const qualities: Quality[] = [];

  for (const status of childrenStatuses) {
    if (status !== "unknown") {
      qualities.push(status);
    }
  }

  return worstOf(qualities);
}
