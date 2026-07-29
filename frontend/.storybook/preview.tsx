import type { Preview } from "@storybook/react";

import "@/app/globals.css";

const preview: Preview = {
  parameters: {
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/i,
      },
    },
    backgrounds: {
      default: "bridge",
      values: [
        { name: "bridge", value: "#121418" },
        { name: "panel", value: "#1a1e24" },
      ],
    },
  },
  decorators: [
    (Story) => (
      <div
        data-theme="day"
        data-design="d01"
        style={{ minHeight: "100vh", padding: 16 }}
      >
        <Story />
      </div>
    ),
  ],
};

export default preview;
