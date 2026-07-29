"use client";

import { DesignSwitcher } from "@/components/ds/DesignSwitcher";
import { ThemeSwitcher } from "@/components/ds/ThemeSwitcher";
import { useDesign } from "@/hooks/useDesign";
import { useTheme } from "@/hooks/useTheme";
import { isDesignPreviewEnabled } from "@/lib/theme/switcher-spec";

export function AppearanceControls() {
  const { theme, setTheme } = useTheme();
  const { design, setDesign } = useDesign();
  const preview = isDesignPreviewEnabled();

  return (
    <main
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "var(--gap-grid, 16px)",
        padding: "var(--content-pad-x, 24px)",
        minHeight: "100vh",
        background: "var(--surface-0)",
        color: "var(--text-primary)",
      }}
    >
      <h1 style={{ fontFamily: "var(--font-display)", fontSize: "var(--font-title)" }}>
        Appearance
      </h1>
      <p style={{ color: "var(--text-secondary)", margin: 0 }}>
        Theme and design preview controls
      </p>
      <div style={{ display: "flex", gap: "var(--gap-grid, 16px)", flexWrap: "wrap" }}>
        <ThemeSwitcher theme={theme} onChange={setTheme} />
        {preview ? (
          <DesignSwitcher design={design} onChange={setDesign} enabled />
        ) : null}
      </div>
      <div
        data-testid="alarm-critical-sample"
        style={{ color: "var(--alarm-critical-fg)" }}
      >
        alarm-critical
      </div>
    </main>
  );
}
