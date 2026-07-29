"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import {
  applyDesignAttr,
  readStoredDesign,
  writeStoredDesign,
} from "@/lib/theme/storage";
import { nextDesign, type DesignId } from "@/lib/theme/types";

type DesignContextValue = {
  design: DesignId;
  setDesign: (design: DesignId) => void;
  cycleDesign: () => void;
};

const DesignContext = createContext<DesignContextValue | null>(null);

export function DesignProvider({ children }: { children: ReactNode }) {
  const [design, setDesignState] = useState<DesignId>(() =>
    typeof window === "undefined"
      ? "d01"
      : readStoredDesign(window.localStorage),
  );

  useEffect(() => {
    applyDesignAttr(design, document.documentElement);
    writeStoredDesign(design, window.localStorage);
  }, [design]);

  const setDesign = useCallback((next: DesignId) => {
    setDesignState(next);
  }, []);

  const cycleDesign = useCallback(() => {
    setDesignState((current) => nextDesign(current));
  }, []);

  const value = useMemo(
    () => ({ design, setDesign, cycleDesign }),
    [design, setDesign, cycleDesign],
  );

  return (
    <DesignContext.Provider value={value}>{children}</DesignContext.Provider>
  );
}

export function useDesign(): DesignContextValue {
  const ctx = useContext(DesignContext);
  if (!ctx) {
    throw new Error("useDesign must be used within DesignProvider");
  }
  return ctx;
}
