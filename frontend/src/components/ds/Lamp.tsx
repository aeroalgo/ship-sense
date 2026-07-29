"use client";

import { useEffect, useState, type CSSProperties } from "react";

import {
  LAMP_PULSE,
  LAMP_SIZE_PX,
  LAMP_TEST_ID,
  LIFECYCLE_OPACITY,
  QUALITY_COLOR_TOKEN,
  QUALITY_OVERLAY_SVG,
  SEVERITY_COLOR_TOKEN,
  SEVERITY_SVG,
  shouldPulse,
  type LampProps,
} from "@/lib/ds/lamp-grammar-spec";

import styles from "./Lamp.module.css";

export type { LampProps };

function usePrefersReducedMotion(): boolean {
  const [reduced, setReduced] = useState(false);

  useEffect(() => {
    if (typeof window.matchMedia !== "function") return;
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    const sync = () => setReduced(mq.matches);
    sync();
    mq.addEventListener("change", sync);
    return () => mq.removeEventListener("change", sync);
  }, []);

  return reduced;
}

function GlyphLayer({
  src,
  color,
  overlay,
}: {
  src: string;
  color: string;
  overlay?: string;
}) {
  return (
    <span
      className={styles.layer}
      data-overlay={overlay}
      style={{
        backgroundColor: color,
        WebkitMaskImage: `url(${src})`,
        maskImage: `url(${src})`,
        WebkitMaskSize: "contain",
        maskSize: "contain",
        WebkitMaskRepeat: "no-repeat",
        maskRepeat: "no-repeat",
        WebkitMaskPosition: "center",
        maskPosition: "center",
      }}
      aria-hidden="true"
    />
  );
}

export function Lamp({
  severity,
  lifecycle,
  quality,
  size = "md",
  reconstructed = false,
}: LampProps) {
  const reducedMotion = usePrefersReducedMotion();
  const pulseWanted = shouldPulse(severity, lifecycle);
  const pulseAttr = pulseWanted
    ? reducedMotion
      ? "static"
      : "on"
    : "off";
  const px = LAMP_SIZE_PX[size];
  const overlaySrc = QUALITY_OVERLAY_SVG[quality];
  const overlayColor = QUALITY_COLOR_TOKEN[quality];

  return (
    <span
      data-testid={LAMP_TEST_ID}
      data-severity={severity}
      data-lifecycle={lifecycle}
      data-quality={quality}
      data-state={`${severity}:${quality}`}
      data-pulse={pulseAttr}
      data-reconstructed={reconstructed ? "true" : undefined}
      className={[
        styles.root,
        styles[`quality_${quality}`],
        pulseAttr === "on" ? styles.pulse : null,
        pulseAttr === "static" ? styles.pulseStatic : null,
      ]
        .filter(Boolean)
        .join(" ")}
      style={
        {
          width: px,
          height: px,
          opacity: LIFECYCLE_OPACITY[lifecycle],
          [LAMP_PULSE.cssVar]: `${LAMP_PULSE.periodMs}ms`,
        } as CSSProperties
      }
      role="img"
      aria-label={`${severity}, ${quality}, ${lifecycle}`}
    >
      <GlyphLayer
        src={SEVERITY_SVG[severity]}
        color={SEVERITY_COLOR_TOKEN[severity]}
      />
      {overlaySrc && overlayColor ? (
        <GlyphLayer
          src={overlaySrc}
          color={overlayColor}
          overlay={quality}
        />
      ) : null}
    </span>
  );
}
