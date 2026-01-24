/**
 * Type definitions for Ledger components
 */

export type LedgerType = 'glass' | 'human' | 'catalyst' | 'exchange';
export type AlertLevel = 'normal' | 'warning' | 'critical';
export type ComponentState = 'loading' | 'error' | 'empty' | 'live';

/**
 * Base ledger data structure
 * Specific ledger types will extend this with additional properties
 */
export interface BaseLedgerData {
  id: string;
  timestamp: Date;
  lastUpdated?: Date;
}

/**
 * Glass Ledger data (TVL and fees)
 */
export interface GlassLedgerData extends BaseLedgerData {
  tvl: number;
  fees: number;
  revenue: number;
  tvlChange24h: number;
  feesChange24h: number;
  historicalData?: Array<{
    date: string;
    tvl: number;
    fees: number;
  }>;
}

/**
 * Human Ledger data (sentiment)
 */
export interface HumanLedgerData extends BaseLedgerData {
  sentiment: 'bullish' | 'bearish' | 'neutral';
  sentimentScore: number; // -1 to 1
  trendingCoins: string[];
  newsVolume: number;
  heatmapData?: Array<{
    date: string;
    sentiment: number;
  }>;
}

/**
 * Catalyst Ledger data (events)
 */
export interface CatalystLedgerData extends BaseLedgerData {
  events: Array<{
    id: string;
    title: string;
    type: 'listing' | 'regulation' | 'upgrade' | 'other';
    priority: 'low' | 'medium' | 'high' | 'critical';
    timestamp: Date;
    description?: string;
  }>;
}

/**
 * Exchange Ledger data (prices)
 */
export interface ExchangeLedgerData extends BaseLedgerData {
  portfolioValue: number;
  topGainer: {
    symbol: string;
    change: number;
  };
  topLoser: {
    symbol: string;
    change: number;
  };
  sparklines: Array<{
    symbol: string;
    prices: number[];
    currentPrice: number;
    change24h: number;
  }>;
}

/**
 * Union type for all ledger data
 */
export type LedgerData = GlassLedgerData | HumanLedgerData | CatalystLedgerData | ExchangeLedgerData;

/**
 * Props for LedgerCard component
 */
export interface LedgerCardProps {
  /** Type of ledger to display */
  ledgerType: LedgerType;
  /** Ledger data to display */
  data?: LedgerData;
  /** Callback when user clicks to drill down into details */
  onDrillDown?: (id: string) => void;
  /** Alert level for visual indication (used mainly for Catalyst) */
  alertLevel?: AlertLevel;
  /** Loading state */
  isLoading?: boolean;
  /** Error state */
  error?: Error | null;
  /** Show table view instead of chart */
  showTableView?: boolean;
  /** Callback when table view is toggled */
  onToggleTableView?: () => void;
}

/**
 * Configuration for ledger appearance
 */
export interface LedgerConfig {
  color: string;
  icon: string;
  label: string;
  description: string;
}

/**
 * Ledger color and styling configuration
 */
export const LEDGER_CONFIG: Record<LedgerType, LedgerConfig> = {
  glass: {
    color: '#3b82f6',
    icon: '🔷',
    label: 'Glass Ledger',
    description: 'On-chain and fundamental protocol metrics',
  },
  human: {
    color: '#10b981',
    icon: '👥',
    label: 'Human Ledger',
    description: 'Social sentiment and narrative streams',
  },
  catalyst: {
    color: '#f59e0b',
    icon: '⚡',
    label: 'Catalyst Ledger',
    description: 'Real-time event detection',
  },
  exchange: {
    color: '#8b5cf6',
    icon: '💱',
    label: 'Exchange Ledger',
    description: 'Market microstructure and execution data',
  },
};
