import type { Meta, StoryObj } from "@storybook/react"
import { CatalystLedgerCard } from "./CatalystLedgerCard"
import { ExchangeLedgerCard } from "./ExchangeLedgerCard"
import { GlassLedgerCard } from "./GlassLedgerCard"
import { HumanLedgerCard } from "./HumanLedgerCard"
import { LedgerCard } from "./LedgerCard"
import type {
  CatalystLedgerData,
  ExchangeLedgerData,
  GlassLedgerData,
  HumanLedgerData,
} from "./types"

const meta: Meta<typeof LedgerCard> = {
  title: "Components/Ledgers/LedgerCard",
  component: LedgerCard,
  tags: ["autodocs"],
  argTypes: {
    ledgerType: {
      control: "select",
      options: ["glass", "human", "catalyst", "exchange"],
    },
    alertLevel: {
      control: "select",
      options: ["normal", "warning", "critical"],
    },
    isLoading: { control: "boolean" },
    showTableView: { control: "boolean" },
  },
}

export default meta
type Story = StoryObj<typeof LedgerCard>

/**
 * MOCK DATA
 */
const mockGlassData: GlassLedgerData = {
  id: "glass-1",
  timestamp: new Date(),
  lastUpdated: new Date(),
  tvl: 1250000000,
  fees: 45000,
  revenue: 15000,
  tvlChange24h: 2.5,
  feesChange24h: 1.2,
  historicalData: Array.from({ length: 30 }, (_, i) => ({
    date: new Date(Date.now() - i * 86400000).toISOString(),
    tvl: 1000000000 + Math.random() * 500000000,
    fees: 40000 + Math.random() * 10000,
  })).reverse(),
}

const mockHumanData: HumanLedgerData = {
  id: "human-1",
  timestamp: new Date(),
  sentiment: "bullish",
  sentimentScore: 0.75,
  trendingCoins: ["BTC", "ETH", "SOL"],
  newsVolume: 120,
  heatmapData: Array.from({ length: 90 }, (_, i) => ({
    date: new Date(Date.now() - i * 86400000).toISOString(),
    sentiment: Math.random() * 2 - 1,
  })),
}

const mockCatalystData: CatalystLedgerData = {
  id: "catalyst-1",
  timestamp: new Date(),
  events: [
    {
      id: "e1",
      title: "Waitlist Spike",
      priority: "high",
      type: "other",
      timestamp: new Date(),
      description: "Sudden increase in signups",
    },
    {
      id: "e2",
      title: "New Governance Proposal",
      priority: "medium",
      type: "upgrade",
      timestamp: new Date(),
    },
    {
      id: "e3",
      title: "Protocol Upgrade",
      priority: "critical",
      type: "upgrade",
      timestamp: new Date(),
    },
  ],
}

const mockExchangeData: ExchangeLedgerData = {
  id: "exchange-1",
  timestamp: new Date(),
  portfolioValue: 54321,
  topGainer: { symbol: "BTC", change: 5.4 },
  topLoser: { symbol: "DOGE", change: -2.1 },
  sparklines: [
    {
      symbol: "BTC",
      currentPrice: 50123,
      change24h: 5.4,
      prices: Array.from({ length: 20 }, () => 50000 + Math.random() * 1000),
    },
    {
      symbol: "ETH",
      currentPrice: 3012,
      change24h: 2.1,
      prices: Array.from({ length: 20 }, () => 3000 + Math.random() * 100),
    },
    {
      symbol: "SOL",
      currentPrice: 145,
      change24h: -1.2,
      prices: Array.from({ length: 20 }, () => 145 + Math.random() * 5),
    },
    {
      symbol: "DOGE",
      currentPrice: 0.12,
      change24h: -2.1,
      prices: Array.from({ length: 20 }, () => 0.12 + Math.random() * 0.01),
    },
    {
      symbol: "ADA",
      currentPrice: 0.45,
      change24h: 0.5,
      prices: Array.from({ length: 20 }, () => 0.45 + Math.random() * 0.02),
    },
  ],
}

/**
 * STORIES
 */

// 1. Loading State
export const Loading: Story = {
  args: {
    ledgerType: "glass",
    isLoading: true,
  },
}

// 2. Error State
export const ErrorState: Story = {
  args: {
    ledgerType: "glass",
    error: new Error("Failed to fetch data"),
  },
}

// 3. Empty State
export const Empty: Story = {
  args: {
    ledgerType: "glass",
    data: undefined,
  },
}

// 4. Glass Ledger Live
export const GlassLedger: Story = {
  render: (args) => <GlassLedgerCard {...args} data={mockGlassData} />,
  args: {
    ledgerType: "glass",
  },
}

// 5. Human Ledger Live
export const HumanLedger: Story = {
  render: (args) => <HumanLedgerCard {...args} data={mockHumanData} />,
  args: {
    ledgerType: "human",
  },
}

// 6. Catalyst Ledger Live (Warning)
export const CatalystLedger: Story = {
  render: (args) => <CatalystLedgerCard {...args} data={mockCatalystData} />,
  args: {
    ledgerType: "catalyst",
    alertLevel: "warning",
  },
}

// 7. Exchange Ledger Live
export const ExchangeLedger: Story = {
  render: (args) => <ExchangeLedgerCard {...args} data={mockExchangeData} />,
  args: {
    ledgerType: "exchange",
  },
}
