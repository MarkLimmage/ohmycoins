import type { Meta, StoryObj } from "@storybook/react";
import { PLTicker } from "./PLTicker";
import { AlgorithmCard } from "./AlgorithmCard";
import { KillSwitch } from "./KillSwitch";
import { AlgorithmGrid } from "./AlgorithmGrid";
import { Box } from "@chakra-ui/react";
import { fn } from '@storybook/test';

// --- PLTicker Stories ---
const metaTicker: Meta<typeof PLTicker> = {
  component: PLTicker,
  title: "Floor/PLTicker",
};
export default metaTicker;
type StoryTicker = StoryObj<typeof PLTicker>;

export const Positive: StoryTicker = {
  args: {
    data: {
      total_pnl: 1234.56,
      pnl_percentage: 0.023,
      active_count: 3,
      paused_count: 1,
      is_connected: true,
      last_update: "2026-01-25T10:00:00Z",
    },
  },
};

export const Negative: StoryTicker = {
  args: {
    data: {
      total_pnl: -542.30,
      pnl_percentage: -0.012,
      active_count: 2,
      paused_count: 2,
      is_connected: true,
      last_update: "2026-01-25T10:00:00Z",
    },
  },
};

export const Disconnected: StoryTicker = {
  args: {
    data: {
      total_pnl: 1234.56,
      pnl_percentage: 0.023,
      active_count: 3,
      paused_count: 1,
      is_connected: false,
      last_update: "2026-01-25T10:00:00Z",
    },
  },
};
