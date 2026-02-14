import type { Meta, StoryObj } from "@storybook/react"
import { StrategyCard } from "./StrategyCard"

const meta: Meta<typeof StrategyCard> = {
  title: "Performance/StrategyCard",
  component: StrategyCard,
  tags: ["autodocs"],
  argTypes: {
    title: { control: "text" },
    sharpe: { control: "number" },
    winRate: { control: "number", min: 0, max: 1 },
    drawdown: { control: "number", min: 0, max: 1 },
  },
}

export default meta
type Story = StoryObj<typeof StrategyCard>

export const GoodPerformance: Story = {
  args: {
    title: "Alpha Boost",
    sharpe: 2.5,
    winRate: 0.65,
    drawdown: 0.1,
  },
}

export const BadPerformance: Story = {
  args: {
    title: "Risky Bet",
    sharpe: 0.5,
    winRate: 0.35,
    drawdown: 0.4,
  },
}
