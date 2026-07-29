import { render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import {
  SELECTED_TAGS_TEST_ID,
  TAG_PICKER_TEST_ID,
  SelectedTags,
  TagPicker,
} from "./TagPicker";

describe("TagPicker / SelectedTags containers", () => {
  it("keeps select and selected chips in separate containers", () => {
    const onAdd = vi.fn();
    const onRemove = vi.fn();

    render(
      <>
        <TagPicker
          tags={[
            { id: "A", name: "Alpha" },
            { id: "B", name: "Beta" },
          ]}
          selected={["A", "B"]}
          onAdd={onAdd}
        />
        <SelectedTags
          tags={[
            { id: "A", name: "Alpha" },
            { id: "B", name: "Beta" },
          ]}
          selected={["A", "B"]}
          onRemove={onRemove}
        />
      </>,
    );

    const picker = screen.getByTestId(TAG_PICKER_TEST_ID);
    const selected = screen.getByTestId(SELECTED_TAGS_TEST_ID);

    expect(picker.contains(selected)).toBe(false);
    expect(within(picker).queryByRole("button")).toBeNull();
    expect(within(picker).getByLabelText("Добавить тег")).toBeInTheDocument();

    const chips = within(selected).getAllByRole("button");
    expect(chips.map((c) => c.textContent)).toEqual(["Alpha", "Beta"]);
  });
});
