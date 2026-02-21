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
  is_active?: boolean
}

export interface CollectorUpdate {
  name?: string
  config?: Record<string, any>
  is_active?: boolean
}
