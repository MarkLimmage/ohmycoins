import type { Meta, StoryObj } from "@storybook/react";
import { AlgorithmCard } from "./AlgorithmCard";
import { fn } from '@storybook/test';

const meta: Meta<typeof AlgorithmCard> = {
  component: AlgorithmCard,
  title: "Floor/AlgorithmCard",
  args: {
      onPause: fn(),
      onResume: fn(),
      onStop: fn(),
  }
};
export default meta;
type Story = StoryObj<typeof AlgorithmCard>;

export const Active: Story = {
  args: {
    algorithm: {
      id: "1",
      name: "BTC Arb v2",
      pnl_amount: 542.30,
      pnl_percentage: 0.018,
      uptime_seconds: 754,
      trade_count: 23,
      win_count: 15,
      loss_count: 8,
      status: "active",
    },
  },
};

export const Paused: Story = {
  args: {
    algorithm: {
      id: "2",
      name: "ETH Grid",
      pnl_amount: 320.50,
      pnl_percentage: 0.009,
      uptime_seconds: 2700,
      trade_count: 12,
      win_count: 8,
      loss_count: 4,
      status: "paused",
    },
  },
};

export const Stopped: Story = {
  args: {
    algorithm: {
      id: "3",
      name: "SOL MeanRev",
      pnl_amount: -120.00,
      pnl_percentage: -0.015,
      uptime_seconds: 400,
      trade_count: 5,
      win_count: 1,
      loss_count: 4,
      status: "stopped",
    },
  },
};

export const ErrorState: Story = {
  args: {
    algorithm: {
      id: "4",
      name: "DOGE Scalper",
      pnl_amount: 0,
      pnl_percentage: 0,
      uptime_seconds: 10,
      trade_count: 0,
      win_count: 0,
      loss_count: 0,
      status: "error",
      status_message: "Insufficient Balance"
    },
  },
};
