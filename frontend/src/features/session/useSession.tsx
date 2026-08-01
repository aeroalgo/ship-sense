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
import { useRouter } from "next/navigation";

import { ApiError, onUnauthorized } from "@/lib/api/client";
import { createSession, deleteSession } from "@/lib/api/session";

export const SESSION_STORAGE_KEY = "shipsense-session-person";
export const SESSION_TIMEOUT_MESSAGE = "Сессия завершена по таймауту";
export const SESSION_TOAST_TEST_ID = "session-toast";

export type SessionPerson = {
  person_id: string;
  name: string;
  rank: string;
  default_screen: number;
};

export function defaultScreenPath(defaultScreen: number): string {
  return defaultScreen === 6 ? "/watch" : "/overview";
}

function readStoredPerson(): SessionPerson | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = sessionStorage.getItem(SESSION_STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as SessionPerson;
    if (
      typeof parsed.person_id !== "string" ||
      typeof parsed.name !== "string" ||
      typeof parsed.rank !== "string" ||
      typeof parsed.default_screen !== "number"
    ) {
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
}

function writeStoredPerson(person: SessionPerson | null): void {
  if (typeof window === "undefined") return;
  if (!person) {
    sessionStorage.removeItem(SESSION_STORAGE_KEY);
    return;
  }
  sessionStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(person));
}

type SessionContextValue = {
  person: SessionPerson | null;
  isReady: boolean;
  toastMessage: string | null;
  clearToast: () => void;
  login: (personId: string) => Promise<string>;
  logout: () => Promise<void>;
};

const SessionContext = createContext<SessionContextValue | null>(null);

export function SessionProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [person, setPerson] = useState<SessionPerson | null>(null);
  const [isReady, setIsReady] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  useEffect(() => {
    setPerson(readStoredPerson());
    setIsReady(true);
  }, []);

  const clearSession = useCallback(() => {
    setPerson(null);
    writeStoredPerson(null);
  }, []);

  const clearToast = useCallback(() => {
    setToastMessage(null);
  }, []);

  useEffect(() => {
    return onUnauthorized((_error: ApiError) => {
      setPerson((current) => {
        if (!current) return current;
        writeStoredPerson(null);
        setToastMessage(SESSION_TIMEOUT_MESSAGE);
        router.push("/login");
        return null;
      });
    });
  }, [router]);

  const login = useCallback(async (personId: string): Promise<string> => {
    const result = await createSession({ person_id: personId });
    const next: SessionPerson = {
      person_id: result.data.person_id,
      name: result.data.name,
      rank: result.data.rank,
      default_screen: result.data.default_screen,
    };
    setPerson(next);
    writeStoredPerson(next);
    setToastMessage(null);
    return defaultScreenPath(next.default_screen);
  }, []);

  const logout = useCallback(async () => {
    try {
      await deleteSession();
    } finally {
      clearSession();
    }
  }, [clearSession]);

  const value = useMemo<SessionContextValue>(
    () => ({
      person,
      isReady,
      toastMessage,
      clearToast,
      login,
      logout,
    }),
    [person, isReady, toastMessage, clearToast, login, logout],
  );

  return (
    <SessionContext.Provider value={value}>
      {toastMessage ? (
        <div
          data-testid={SESSION_TOAST_TEST_ID}
          role="status"
          style={{
            position: "fixed",
            top: 12,
            left: "50%",
            transform: "translateX(-50%)",
            zIndex: 50,
            padding: "12px 16px",
            background: "var(--surface-2)",
            color: "var(--text-primary)",
            border: "var(--border-width, 1px) solid var(--border-strong)",
            borderRadius: "var(--radius-md)",
            fontFamily: "var(--font-sans)",
            fontSize: "var(--font-body)",
            boxShadow: "0 8px 24px color-mix(in srgb, var(--text-primary) 18%, transparent)",
          }}
        >
          {toastMessage}
          <button
            type="button"
            onClick={clearToast}
            aria-label="Закрыть"
            style={{
              marginLeft: 12,
              border: "none",
              background: "transparent",
              color: "var(--text-secondary)",
              cursor: "pointer",
              fontFamily: "inherit",
            }}
          >
            ×
          </button>
        </div>
      ) : null}
      {children}
    </SessionContext.Provider>
  );
}

export function useSession(): SessionContextValue {
  const ctx = useContext(SessionContext);
  if (!ctx) {
    throw new Error("useSession must be used within SessionProvider");
  }
  return ctx;
}
