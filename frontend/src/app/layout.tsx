import type { Metadata } from "next";
import type { ReactNode } from "react";
import { IBM_Plex_Mono, IBM_Plex_Sans } from "next/font/google";
import Script from "next/script";

import { AppearanceProviders } from "@/features/session/AppearanceProviders";
import { QueryProvider } from "@/features/shell/QueryProvider";
import { ANTI_FLASH_SCRIPT } from "@/lib/theme/anti-flash-script";

import "./globals.css";

const plexSans = IBM_Plex_Sans({
  subsets: ["latin", "cyrillic"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-plex-sans",
  display: "swap",
});

const plexMono = IBM_Plex_Mono({
  subsets: ["latin", "cyrillic"],
  weight: ["400", "500", "600"],
  variable: "--font-plex-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "ShipSense",
  description: "ShipSense bridge HMI",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html
      lang="ru"
      data-design="d01"
      data-theme="day"
      className={`${plexSans.variable} ${plexMono.variable}`}
      suppressHydrationWarning
    >
      <body>
        <Script
          id="shipsense-anti-flash"
          strategy="beforeInteractive"
          dangerouslySetInnerHTML={{ __html: ANTI_FLASH_SCRIPT }}
        />
        <AppearanceProviders>
          <QueryProvider>{children}</QueryProvider>
        </AppearanceProviders>
      </body>
    </html>
  );
}
