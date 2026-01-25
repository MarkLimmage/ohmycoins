export interface PLTickerData {
  total_pnl: number; // In AUD
  pnl_percentage: number; // Decimal (0.023 = 2.3%)
  active_count: number;
  paused_count: number;
  is_connected: boolean; // WebSocket connection status
  last_update: string; // ISO 8601 timestamp
}

export type AlgorithmStatus = 'active' | 'paused' | 'stopped' | 'error' | 'initializing';

export interface AlgorithmData {
  id: string;
  name: string;
  pnl_amount: number;
  pnl_percentage: number;
  uptime_seconds: number;
  trade_count: number;
  win_count: number;
  loss_count: number;
  status: AlgorithmStatus;
  status_message?: string; // For errors or pause details
}
