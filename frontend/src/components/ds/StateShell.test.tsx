import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { STATE_SHELL_TEST_ID, STATE_SHELL_VARIANTS } from "./StateShell";
import { StateShell } from "./StateShell";

describe("StateShell", () => {
  it("should render testid for each of 5 variants", () => {
    expect(STATE_SHELL_VARIANTS).toHaveLength(5);

    for (const variant of STATE_SHELL_VARIANTS) {
      const { unmount } = render(
        <StateShell variant={variant}>
          <span>body-{variant}</span>
        </StateShell>,
      );
      const el = screen.getByTestId(STATE_SHELL_TEST_ID);
      expect(el.getAttribute("data-variant")).toBe(variant);
      expect(screen.getByText(`body-${variant}`)).toBeInTheDocument();
      unmount();
    }
  });

  it("should show retry when error and onRetry provided", () => {
    const onRetry = () => undefined;
    const { unmount } = render(
      <StateShell variant="error" onRetry={onRetry} message="Сбой" />,
    );
    expect(screen.getByTestId(STATE_SHELL_TEST_ID)).toHaveAttribute(
      "data-variant",
      "error",
    );
    expect(screen.getByRole("button", { name: /повторить/i })).toBeInTheDocument();
    expect(screen.getByText("Сбой")).toBeInTheDocument();
    unmount();
  });
});
