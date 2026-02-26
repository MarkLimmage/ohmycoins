export interface CollectorPlugin {
  id: string
  name: string
  description: string
  version: string
  schema: Record<string, any> // JSON Schema for configuration
}

export type CollectorStatus = "idle" | "running" | "success" | "failed"

export interface CollectorInstance {
  id: string
  name: string
  plugin_id: string
  status: CollectorStatus
  config: Record<string, any>
  schedule_cron: string // Added schedule_cron
  last_run: string | null
  next_run: string | null
  is_active: boolean
  error_count: number
  success_count: number
}

export interface CollectorStatsPoint {
  timestamp: string
  count: number
}

export interface CollectorCreate {
  name: string
  plugin_id: string
  config: Record<string, any>
  schedule_cron: string // Added schedule_cron
  is_active?: boolean
}

export interface CollectorUpdate {
  name?: string
  config?: Record<string, any>
  schedule_cron?: string // Added schedule_cron
  is_active?: boolean
}

export type ExchangeHealthStatus = "green" | "amber" | "red" | "unknown"

export interface ExchangeHealthInfo {
  status: ExchangeHealthStatus
  lastRunStatus: string | null
  lastRunAt: string | null
  failedCount24h: number
  totalCount24h: number
  details: string
}

export interface CollectorCardData {
  plugin_id: string
  plugin_name: string
  plugin_description: string
  plugin_schema: Record<string, any>
  instance_id: string | null
  instance_name: string | null
  status: CollectorStatus
  config: Record<string, any>
  schedule_cron: string
  last_run: string | null
  is_active: boolean
  success_rate: number | null
  total_records: number | null
  avg_duration: number | null
  total_runs: number | null
}
