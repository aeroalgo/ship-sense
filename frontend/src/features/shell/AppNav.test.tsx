import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const mockPathname = vi.fn(() => "/overview");

vi.mock("next/navigation", () => ({
  usePathname: () => mockPathname(),
}));

import { AppNav, NAV_ITEMS } from "./AppNav";

describe("AppNav", () => {
  afterEach(() => {
    cleanup();
  });

  beforeEach(() => {
    mockPathname.mockReturnValue("/overview");
  });

  it("renders four nav links with stable testids", () => {
    render(<AppNav />);

    expect(screen.getByTestId("nav-overview")).toBeInTheDocument();
    expect(screen.getByTestId("nav-journal")).toBeInTheDocument();
    expect(screen.getByTestId("nav-trends")).toBeInTheDocument();
    expect(screen.getByTestId("nav-watch")).toBeInTheDocument();
    expect(NAV_ITEMS).toHaveLength(4);
  });

  it("marks the active route with app-nav__link--active", () => {
    mockPathname.mockReturnValue("/journal");
    render(<AppNav />);

    expect(screen.getByTestId("nav-journal")).toHaveClass(
      "app-nav__link--active",
    );
    expect(screen.getByTestId("nav-overview")).not.toHaveClass(
      "app-nav__link--active",
    );
  });

  it("uses touch targets of at least 48px via --touch-min", () => {
    render(<AppNav />);
    const link = screen.getByTestId("nav-overview");
    const style = link.getAttribute("style") ?? "";
    expect(style).toMatch(/min-height:\s*var\(--touch-min,\s*48px\)/i);
    expect(style).toMatch(/min-width:\s*var\(--touch-min,\s*48px\)/i);
  });
});
