import type { Meta, StoryObj } from "@storybook/react"
import { fn } from "@storybook/test"
import { AlgorithmGrid } from "./AlgorithmGrid"

const meta: Meta<typeof AlgorithmGrid> = {
  component: AlgorithmGrid,
  title: "Floor/AlgorithmGrid",
  parameters: {
    layout: "fullscreen",
  },
  args: {
    onPause: fn(),
    onResume: fn(),
    onStop: fn(),
  },
}
export default meta
type Story = StoryObj<typeof AlgorithmGrid>

const sampleAlgos = [
  {
    id: "1",
    name: "Algo 1",
    pnl_amount: 100,
    pnl_percentage: 0.1,
    uptime_seconds: 100,
    trade_count: 10,
    win_count: 5,
    loss_count: 5,
    status: "active" as const,
  },
  {
    id: "2",
    name: "Algo 2",
    pnl_amount: 200,
    pnl_percentage: 0.2,
    uptime_seconds: 200,
    trade_count: 20,
    win_count: 10,
    loss_count: 10,
    status: "paused" as const,
  },
  {
    id: "3",
    name: "Algo 3",
    pnl_amount: -50,
    pnl_percentage: -0.05,
    uptime_seconds: 300,
    trade_count: 5,
    win_count: 2,
    loss_count: 3,
    status: "stopped" as const,
  },
]

export const Desktop: Story = {
  args: {
    algorithms: sampleAlgos,
  },
}

export const MobileView: Story = {
  parameters: {
    viewport: {
      defaultViewport: "mobile1",
    },
  },
  args: {
    algorithms: sampleAlgos,
  },
}
