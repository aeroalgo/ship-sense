"use client";

import { useEffect, useState } from "react";

export type ComputeStaleInput = {
  lastFreshTs: string | null;
  nowMs: number;
  thresholdSec: number;
  forceStale: boolean;
};

export function readStaleThresholdSec(): number {
  const raw = process.env.NEXT_PUBLIC_STALE_THRESHOLD_SEC;
  if (raw === undefined || raw === "") {
    throw new Error("NEXT_PUBLIC_STALE_THRESHOLD_SEC is not set");
  }
  const n = Number(raw);
  if (!Number.isFinite(n) || n <= 0) {
    throw new Error(`NEXT_PUBLIC_STALE_THRESHOLD_SEC invalid: ${raw}`);
  }
  return n;
}

export function computeStale(input: ComputeStaleInput): boolean {
  if (input.forceStale) return true;
  if (!input.lastFreshTs) return false;
  const lastMs = Date.parse(input.lastFreshTs);
  if (Number.isNaN(lastMs)) {
    throw new Error(`Invalid lastFreshTs: ${input.lastFreshTs}`);
  }
  return input.nowMs - lastMs >= input.thresholdSec * 1000;
}

export type UseStaleGateInput = {
  lastFreshTs: string | null;
  forceStale?: boolean;
};

export type UseStaleGateResult = {
  stale: boolean;
  lastTs: string | null;
};

export function useStaleGate(input: UseStaleGateInput): UseStaleGateResult {
  const thresholdSec = readStaleThresholdSec();
  const forceStale = input.forceStale ?? false;
  const [nowMs, setNowMs] = useState(() => Date.now());

  useEffect(() => {
    const id = window.setInterval(() => {
      setNowMs(Date.now());
    }, 1000);
    return () => window.clearInterval(id);
  }, []);

  const stale = computeStale({
    lastFreshTs: input.lastFreshTs,
    nowMs,
    thresholdSec,
    forceStale,
  });

  useEffect(() => {
    document.body.setAttribute("data-stale", stale ? "true" : "false");
    return () => {
      document.body.removeAttribute("data-stale");
    };
  }, [stale]);

  return { stale, lastTs: input.lastFreshTs };
}
