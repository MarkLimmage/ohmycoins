/**
 * Demo page showcasing all implemented components
 * Sprint 2.15 - Track B: Core Component Library
 */

import { Box, Container, Grid, Heading, Text, VStack } from "@chakra-ui/react"
import { useState } from "react"
// Safety Buttons
import { ConfirmTrade, EmergencyStop, KillSwitch } from "../components/Floor"
// Agent Terminal
import { AgentTerminal } from "../components/Lab"
// Ledger Components
import {
  CatalystLedgerCard,
  ExchangeLedgerCard,
  GlassLedgerCard,
  HumanLedgerCard,
} from "../components/Ledgers"
import type {
  CatalystLedgerData,
  ExchangeLedgerData,
  GlassLedgerData,
  HumanLedgerData,
} from "../components/Ledgers/types"

// Global keyboard shortcuts
import {
  KeyboardShortcutHints,
  TableViewProvider,
  useTableView,
} from "../hooks/useGlobalKeyboardShortcuts"

/**
 * Mock data for demonstrations
 */
const mockGlassData: GlassLedgerData = {
  id: "glass-1",
  timestamp: new Date(),
  lastUpdated: new Date(Date.now() - 30000), // 30 seconds ago
  tvl: 42500000000, // $42.5B
  fees: 12300000, // $12.3M
  revenue: 8500000,
  tvlChange24h: 2.3,
  feesChange24h: 5.7,
  historicalData: [
    { date: "2026-01-20", tvl: 40000000000, fees: 11000000 },
    { date: "2026-01-21", tvl: 40500000000, fees: 11500000 },
    { date: "2026-01-22", tvl: 41000000000, fees: 11800000 },
    { date: "2026-01-23", tvl: 41800000000, fees: 11900000 },
    { date: "2026-01-24", tvl: 42500000000, fees: 12300000 },
  ],
}

const mockHumanData: HumanLedgerData = {
  id: "human-1",
  timestamp: new Date(),
  lastUpdated: new Date(Date.now() - 120000), // 2 minutes ago
  sentiment: "bullish",
  sentimentScore: 0.65,
  trendingCoins: ["BTC", "ETH", "SOL", "AVAX"],
  newsVolume: 143,
  heatmapData: [
    { date: "2026-01-20", sentiment: 0.3 },
    { date: "2026-01-21", sentiment: 0.4 },
    { date: "2026-01-22", sentiment: 0.5 },
    { date: "2026-01-23", sentiment: 0.6 },
    { date: "2026-01-24", sentiment: 0.65 },
  ],
}

const mockCatalystData: CatalystLedgerData = {
  id: "catalyst-1",
  timestamp: new Date(),
  lastUpdated: new Date(Date.now() - 15000), // 15 seconds ago
  events: [
    {
      id: "evt-1",
      title: "New BTC listing on CoinSpot",
      type: "listing",
      priority: "critical",
      timestamp: new Date(Date.now() - 300000),
      description: "Bitcoin Cash (BCH) now available for trading",
    },
    {
      id: "evt-2",
      title: "SEC filing detected",
      type: "regulation",
      priority: "high",
      timestamp: new Date(Date.now() - 600000),
      description: "New crypto ETF application submitted",
    },
    {
      id: "evt-3",
      title: "Ethereum network upgrade",
      type: "upgrade",
      priority: "medium",
      timestamp: new Date(Date.now() - 900000),
      description: "EIP-4844 scheduled for next week",
    },
  ],
}

const mockExchangeData: ExchangeLedgerData = {
  id: "exchange-1",
  timestamp: new Date(),
  lastUpdated: new Date(Date.now() - 5000), // 5 seconds ago
  portfolioValue: 125430.5,
  topGainer: {
    symbol: "SOL",
    change: 8.5,
  },
  topLoser: {
    symbol: "ADA",
    change: -3.2,
  },
  sparklines: [
    {
      symbol: "BTC",
      prices: [45000, 45200, 45100, 45400, 45500, 45300, 45600],
      currentPrice: 45600,
      change24h: 1.8,
    },
    {
      symbol: "ETH",
      prices: [2800, 2820, 2810, 2850, 2860, 2840, 2870],
      currentPrice: 2870,
      change24h: 2.5,
    },
    {
      symbol: "SOL",
      prices: [95, 98, 100, 102, 103, 104, 105],
      currentPrice: 105,
      change24h: 8.5,
    },
  ],
}

/**
 * Inner component that uses the TableViewProvider context
 */
function ComponentShowcaseContent() {
  const { showTableViews } = useTableView()
  const [isKillSwitchActive, setIsKillSwitchActive] = useState(true)

  // Safety button handlers
  const handleEmergencyStop = async () => {
    console.log("🚨 EMERGENCY STOP TRIGGERED")
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 1000))
    setIsKillSwitchActive(false)
    console.log("✅ All systems stopped")
  }

  const handleConfirmTrade = async () => {
    console.log("✅ Trade confirmed")
    await new Promise((resolve) => setTimeout(resolve, 500))
  }

  return (
    <Box minH="100vh" bg="gray.50" py={8}>
      <Container maxW="container.xl">
        <VStack gap={8} align="stretch">
          {/* Header */}
          <Box>
            <Heading size="2xl" mb={2}>
              Component Library Demo
            </Heading>
            <Text color="gray.600" fontSize="lg">
              Sprint 2.15 - Track B: Core Component Library Implementation
            </Text>
            <Text color="gray.500" fontSize="sm" mt={2}>
              {showTableViews ? "📊 Table View Mode" : "📈 Chart View Mode"} •
              Press Ctrl+Shift+T to toggle
            </Text>
          </Box>

          {/* LedgerCard Section */}
          <Box>
            <Heading size="xl" mb={4}>
              1. LedgerCard Components
            </Heading>
            <Text color="gray.600" mb={4}>
              Four variants with loading, error, empty, and live states.
              Includes table view toggle (REQ-UX-001).
            </Text>

            <Grid
              templateColumns="repeat(auto-fit, minmax(300px, 1fr))"
              gap={6}
            >
              <GlassLedgerCard
                ledgerType="glass"
                data={mockGlassData}
                showTableView={showTableViews}
              />
              <HumanLedgerCard
                ledgerType="human"
                data={mockHumanData}
                showTableView={showTableViews}
              />
              <CatalystLedgerCard
                ledgerType="catalyst"
                data={mockCatalystData}
                showTableView={showTableViews}
              />
              <ExchangeLedgerCard
                ledgerType="exchange"
                data={mockExchangeData}
                showTableView={showTableViews}
              />
            </Grid>
          </Box>

          {/* Loading State Example */}
          <Box>
            <Heading size="lg" mb={4}>
              Loading States
            </Heading>
            <Grid
              templateColumns="repeat(auto-fit, minmax(300px, 1fr))"
              gap={6}
            >
              <GlassLedgerCard ledgerType="glass" isLoading />
              <HumanLedgerCard ledgerType="human" isLoading />
            </Grid>
          </Box>

          {/* Error State Example */}
          <Box>
            <Heading size="lg" mb={4}>
              Error States
            </Heading>
            <Grid
              templateColumns="repeat(auto-fit, minmax(300px, 1fr))"
              gap={6}
            >
              <CatalystLedgerCard
                ledgerType="catalyst"
                error={new Error("Failed to fetch catalyst data")}
              />
              <ExchangeLedgerCard
                ledgerType="exchange"
                error={new Error("Connection timeout")}
              />
            </Grid>
          </Box>

          {/* AgentTerminal Section */}
          <Box>
            <Heading size="xl" mb={4}>
              2. AgentTerminal Component
            </Heading>
            <Text color="gray.600" mb={4}>
              Streaming console for agent logs with search, copy, and
              auto-scroll features.
            </Text>

            <Box h="500px">
              <AgentTerminal
                sessionId="demo-session-1"
                streamUrl="wss://example.com/agent/stream"
                allowInteraction={true}
              />
            </Box>
          </Box>

          {/* SafetyButton Section */}
          <Box>
            <Heading size="xl" mb={4}>
              3. SafetyButton Components
            </Heading>
            <Text color="gray.600" mb={4}>
              Fail-safe controls for trading operations with confirmation flows
              and cooldowns.
            </Text>

            <VStack gap={6} align="stretch">
              {/* ConfirmTrade */}
              <Box p={6} bg="white" borderRadius="lg" shadow="sm">
                <Heading size="md" mb={3}>
                  ConfirmTrade Button
                </Heading>
                <Text color="gray.600" mb={4}>
                  Two-step confirmation for trade actions
                </Text>
                <ConfirmTrade
                  onConfirm={handleConfirmTrade}
                  tradeDetails="BTC Buy Order - $45,600"
                />
              </Box>

              {/* EmergencyStop */}
              <Box p={6} bg="white" borderRadius="lg" shadow="sm">
                <Heading size="md" mb={3}>
                  EmergencyStop Button
                </Heading>
                <Text color="gray.600" mb={4}>
                  Requires typing "STOP" to confirm
                </Text>
                <EmergencyStop onStop={handleEmergencyStop} />
              </Box>

              {/* KillSwitch */}
              <Box p={6} bg="white" borderRadius="lg" shadow="sm">
                <Heading size="md" mb={3}>
                  KillSwitch (Fixed Position)
                </Heading>
                <Text color="gray.600" mb={4}>
                  Large emergency button, always visible in bottom-right corner.
                  Press Ctrl+Shift+K to focus.
                </Text>
                <Text color="gray.500" fontSize="sm">
                  Scroll down to see the fixed Kill Switch button in the
                  bottom-right corner →
                </Text>
              </Box>
            </VStack>
          </Box>

          {/* Accessibility Features */}
          <Box p={6} bg="blue.50" borderRadius="lg">
            <Heading size="lg" mb={4}>
              ♿ Accessibility Features
            </Heading>
            <Grid
              templateColumns="repeat(auto-fit, minmax(250px, 1fr))"
              gap={4}
            >
              <Box>
                <Text fontWeight="bold" mb={2}>
                  ✅ REQ-UX-001
                </Text>
                <Text fontSize="sm" color="gray.700">
                  Table view toggle for all charts (Ctrl+Shift+T)
                </Text>
              </Box>
              <Box>
                <Text fontWeight="bold" mb={2}>
                  ✅ REQ-UX-004
                </Text>
                <Text fontSize="sm" color="gray.700">
                  Global keyboard shortcuts (Ctrl+Shift+K, Ctrl+Shift+T)
                </Text>
              </Box>
              <Box>
                <Text fontWeight="bold" mb={2}>
                  ✅ REQ-UX-005
                </Text>
                <Text fontSize="sm" color="gray.700">
                  Full keyboard navigation (Tab, Enter, Esc)
                </Text>
              </Box>
              <Box>
                <Text fontWeight="bold" mb={2}>
                  ✅ WCAG 2.1 AA
                </Text>
                <Text fontSize="sm" color="gray.700">
                  ARIA labels, focus indicators, screen reader support
                </Text>
              </Box>
            </Grid>
          </Box>

          {/* Spacer for scrolling */}
          <Box h="200px" />
        </VStack>
      </Container>

      {/* KillSwitch - Fixed Position */}
      {isKillSwitchActive && (
        <KillSwitch
          onKill={handleEmergencyStop}
          isDisabled={!isKillSwitchActive}
        />
      )}

      {/* Keyboard Shortcut Hints */}
      <KeyboardShortcutHints />
    </Box>
  )
}

/**
 * Main component with TableViewProvider wrapper
 */
export function ComponentShowcase() {
  return (
    <TableViewProvider>
      <ComponentShowcaseContent />
    </TableViewProvider>
  )
}

export default ComponentShowcase
