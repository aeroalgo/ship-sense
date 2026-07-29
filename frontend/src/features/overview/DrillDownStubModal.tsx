"use client";

export const DRILL_STUB_TEST_ID = "drill-stub-modal";
export const DRILL_STUB_COPY = "Мнемосхема: фаза 2";

export type DrillDownStubModalProps = {
  open: boolean;
  groupName: string | null;
  onClose: () => void;
};

export function DrillDownStubModal({
  open,
  groupName,
  onClose,
}: DrillDownStubModalProps) {
  if (!open) return null;

  return (
    <div
      data-testid={DRILL_STUB_TEST_ID}
      role="dialog"
      aria-modal="true"
      aria-label={DRILL_STUB_COPY}
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 40,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "color-mix(in srgb, var(--surface-0) 70%, transparent)",
        padding: "var(--panel-pad, 16px)",
      }}
    >
      <div
        style={{
          minWidth: "min(420px, 100%)",
          padding: "var(--panel-pad, 16px)",
          background: "var(--surface-1)",
          color: "var(--text-primary)",
          border: "var(--border-width, 1px) solid var(--border-strong)",
          borderRadius: "var(--radius-md)",
          fontFamily: "var(--font-sans)",
          display: "flex",
          flexDirection: "column",
          gap: "var(--space-3, 12px)",
        }}
      >
        <p style={{ margin: 0, fontSize: "var(--font-title, 1.25rem)" }}>
          {DRILL_STUB_COPY}
        </p>
        {groupName ? (
          <p style={{ margin: 0, color: "var(--text-secondary)" }}>
            Группа: {groupName}
          </p>
        ) : null}
        <button
          type="button"
          onClick={onClose}
          style={{
            alignSelf: "flex-start",
            minHeight: "var(--touch-min, 48px)",
            minWidth: "var(--touch-min, 48px)",
            padding: "0 var(--panel-pad, 16px)",
            border: "var(--border-width, 1px) solid var(--border-strong)",
            borderRadius: "var(--radius-md)",
            background: "var(--surface-2)",
            color: "var(--text-primary)",
            fontFamily: "var(--font-sans)",
            fontSize: "var(--font-body)",
            cursor: "pointer",
          }}
        >
          Закрыть
        </button>
      </div>
    </div>
  );
}
