export const TAG_PICKER_TEST_ID = "tag-picker";
export const SELECTED_TAGS_TEST_ID = "selected-tags";

export type TagPickerItem = {
  id: string;
  name: string;
};

export type TagPickerProps = {
  tags: TagPickerItem[];
  selected?: string[];
  onAdd: (tagId: string) => void;
};

export type SelectedTagsProps = {
  tags: TagPickerItem[];
  selected: string[];
  onRemove: (tagId: string) => void;
};

export function TagPicker({
  tags,
  selected = [],
  onAdd,
}: TagPickerProps) {
  const available = tags.filter((t) => !selected.includes(t.id));

  return (
    <div
      data-testid={TAG_PICKER_TEST_ID}
      style={{
        fontFamily: "var(--font-sans)",
        color: "var(--text-primary)",
      }}
    >
      <select
        aria-label="Добавить тег"
        value=""
        onChange={(e) => {
          if (e.target.value) onAdd(e.target.value);
        }}
        style={{
          width: "100%",
          minHeight: "var(--touch-min, 48px)",
          padding: "0 10px",
          border: "var(--border-width, 1px) solid var(--border-subtle)",
          borderRadius: "var(--radius-sm)",
          background: "var(--surface-1)",
          color: "var(--text-primary)",
          fontFamily: "inherit",
          fontSize: "var(--font-body)",
        }}
      >
        <option value="">Добавить тег…</option>
        {available.map((tag) => (
          <option key={tag.id} value={tag.id}>
            {tag.name}
          </option>
        ))}
      </select>
    </div>
  );
}

export function SelectedTags({ tags, selected, onRemove }: SelectedTagsProps) {
  if (selected.length === 0) {
    return null;
  }

  return (
    <div
      data-testid={SELECTED_TAGS_TEST_ID}
      aria-label="Выбранные теги"
      style={{
        display: "flex",
        flexWrap: "wrap",
        gap: 6,
        fontFamily: "var(--font-sans)",
        color: "var(--text-primary)",
      }}
    >
      {selected.map((id) => {
        const tag = tags.find((t) => t.id === id);
        return (
          <button
            key={id}
            type="button"
            data-tag-id={id}
            onClick={() => onRemove(id)}
            style={{
              minHeight: "var(--touch-min, 48px)",
              padding: "0 12px",
              border: "var(--border-width, 1px) solid var(--border-strong)",
              borderRadius: "var(--radius-sm)",
              background: "var(--surface-2)",
              color: "var(--text-primary)",
              cursor: "pointer",
              fontFamily: "inherit",
            }}
          >
            {tag?.name ?? id}
          </button>
        );
      })}
    </div>
  );
}
