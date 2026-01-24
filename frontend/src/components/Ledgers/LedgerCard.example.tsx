/**
 * Example usage of LedgerCard components
 * This file demonstrates how to use the different ledger card variants
 */

import React from 'react';
import { Box, Grid } from '@chakra-ui/react';
import {
  GlassLedgerCard,
  HumanLedgerCard,
  CatalystLedgerCard,
  ExchangeLedgerCard,
  type GlassLedgerData,
  type HumanLedgerData,
  type CatalystLedgerData,
  type ExchangeLedgerData,
} from './index';

// Mock data for Glass Ledger
const mockGlassData: GlassLedgerData = {
  id: 'glass-1',
  timestamp: new Date(),
  lastUpdated: new Date(),
  tvl: 42500000000, // $42.5B
  fees: 12300000, // $12.3M
  revenue: 8500000, // $8.5M
  tvlChange24h: 5.23,
  feesChange24h: -2.15,
};

// Mock data for Human Ledger
const mockHumanData: HumanLedgerData = {
  id: 'human-1',
  timestamp: new Date(),
  lastUpdated: new Date(),
  sentiment: 'bullish',
  sentimentScore: 0.73,
  trendingCoins: ['BTC', 'ETH', 'SOL', 'AVAX', 'MATIC'],
  newsVolume: 1247,
};

// Mock data for Catalyst Ledger
const mockCatalystData: CatalystLedgerData = {
  id: 'catalyst-1',
  timestamp: new Date(),
  lastUpdated: new Date(),
  events: [
    {
      id: 'event-1',
      title: 'SEC Approves Bitcoin ETF',
      type: 'regulation',
      priority: 'critical',
      timestamp: new Date(Date.now() - 1000 * 60 * 15), // 15 minutes ago
      description: 'The SEC has approved the first spot Bitcoin ETF for trading.',
    },
    {
      id: 'event-2',
      title: 'Ethereum Shanghai Upgrade Complete',
      type: 'upgrade',
      priority: 'high',
      timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2), // 2 hours ago
      description: 'The Shanghai upgrade has been successfully deployed.',
    },
    {
      id: 'event-3',
      title: 'New Token Listing: ARB on Coinbase',
      type: 'listing',
      priority: 'medium',
      timestamp: new Date(Date.now() - 1000 * 60 * 60 * 5), // 5 hours ago
    },
  ],
};

// Mock data for Exchange Ledger
const mockExchangeData: ExchangeLedgerData = {
  id: 'exchange-1',
  timestamp: new Date(),
  lastUpdated: new Date(),
  portfolioValue: 125000,
  topGainer: {
    symbol: 'SOL',
    change: 15.32,
  },
  topLoser: {
    symbol: 'ADA',
    change: -8.45,
  },
  sparklines: [
    {
      symbol: 'BTC',
      prices: [45000, 45200, 45100, 45500, 45800, 46000, 45900],
      currentPrice: 45900,
      change24h: 2.15,
    },
    {
      symbol: 'ETH',
      prices: [2400, 2420, 2390, 2450, 2480, 2500, 2490],
      currentPrice: 2490,
      change24h: 3.75,
    },
    {
      symbol: 'SOL',
      prices: [95, 98, 102, 105, 108, 110, 115],
      currentPrice: 115,
      change24h: 15.32,
    },
    {
      symbol: 'ADA',
      prices: [0.65, 0.64, 0.62, 0.60, 0.59, 0.58, 0.57],
      currentPrice: 0.57,
      change24h: -8.45,
    },
  ],
};

/**
 * Example: 4 Ledgers Dashboard Grid
 */
export function LedgersDashboardExample() {
  const [showTableView, setShowTableView] = React.useState<{
    glass: boolean;
    human: boolean;
    catalyst: boolean;
    exchange: boolean;
  }>({
    glass: false,
    human: false,
    catalyst: false,
    exchange: false,
  });

  const handleDrillDown = (id: string) => {
    console.log('Drill down into:', id);
    // Navigate to detail view or open modal
  };

  return (
    <Box padding="24px">
      <Grid
        templateColumns="repeat(2, 1fr)"
        gap="24px"
        role="region"
        aria-label="4 Ledgers Dashboard"
      >
        <GlassLedgerCard
          ledgerType="glass"
          data={mockGlassData}
          onDrillDown={handleDrillDown}
          showTableView={showTableView.glass}
          onToggleTableView={() =>
            setShowTableView((prev) => ({ ...prev, glass: !prev.glass }))
          }
        />

        <HumanLedgerCard
          ledgerType="human"
          data={mockHumanData}
          onDrillDown={handleDrillDown}
          showTableView={showTableView.human}
          onToggleTableView={() =>
            setShowTableView((prev) => ({ ...prev, human: !prev.human }))
          }
        />

        <CatalystLedgerCard
          ledgerType="catalyst"
          data={mockCatalystData}
          onDrillDown={handleDrillDown}
          alertLevel="critical"
          showTableView={showTableView.catalyst}
          onToggleTableView={() =>
            setShowTableView((prev) => ({ ...prev, catalyst: !prev.catalyst }))
          }
        />

        <ExchangeLedgerCard
          ledgerType="exchange"
          data={mockExchangeData}
          onDrillDown={handleDrillDown}
          showTableView={showTableView.exchange}
          onToggleTableView={() =>
            setShowTableView((prev) => ({ ...prev, exchange: !prev.exchange }))
          }
        />
      </Grid>
    </Box>
  );
}

/**
 * Example: Loading State
 */
export function LoadingStateExample() {
  return (
    <Box padding="24px">
      <Grid templateColumns="repeat(2, 1fr)" gap="24px">
        <GlassLedgerCard ledgerType="glass" isLoading={true} />
        <HumanLedgerCard ledgerType="human" isLoading={true} />
        <CatalystLedgerCard ledgerType="catalyst" isLoading={true} />
        <ExchangeLedgerCard ledgerType="exchange" isLoading={true} />
      </Grid>
    </Box>
  );
}

/**
 * Example: Error State
 */
export function ErrorStateExample() {
  const error = new Error('Failed to fetch ledger data');

  return (
    <Box padding="24px">
      <Grid templateColumns="repeat(2, 1fr)" gap="24px">
        <GlassLedgerCard ledgerType="glass" error={error} />
        <HumanLedgerCard ledgerType="human" error={error} />
        <CatalystLedgerCard ledgerType="catalyst" error={error} />
        <ExchangeLedgerCard ledgerType="exchange" error={error} />
      </Grid>
    </Box>
  );
}

/**
 * Example: Empty State
 */
export function EmptyStateExample() {
  return (
    <Box padding="24px">
      <Grid templateColumns="repeat(2, 1fr)" gap="24px">
        <GlassLedgerCard ledgerType="glass" data={undefined} />
        <HumanLedgerCard ledgerType="human" data={undefined} />
        <CatalystLedgerCard ledgerType="catalyst" data={undefined} />
        <ExchangeLedgerCard ledgerType="exchange" data={undefined} />
      </Grid>
    </Box>
  );
}
