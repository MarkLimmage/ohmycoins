import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { CollectorsService } from "../client/sdk.gen"
import type {
  CollectorsCreateInstanceData,
  CollectorsToggleInstanceData,
  CollectorsTriggerInstanceData,
  CollectorsUpdateInstanceData,
} from "../client/types.gen"
import { useAutoRefresh } from "../context/AutoRefreshContext"
import type {
  ExchangeHealthInfo,
  ExchangeHealthStatus,
} from "../features/admin/types"

// Type definitions for new stats endpoints
export interface VolumeDataPoint {
  time: string
  Glass: number
  Human: number
  Catalyst: number
  Exchange: number
}

export interface ActivityLog {
  id: number
  timestamp: string
  collector: string
  status: string
  items: number
  duration: number
}

export interface AggregateStats {
  collector_name: string
  total_runs: number
  success_count: number
  error_count: number
  total_records: number
  avg_duration_seconds: number
  last_success_at: string | null
  uptime_pct: number
}

export const useCollectorInstances = () => {
  const { isEnabled, interval } = useAutoRefresh()
  return useQuery({
    queryKey: ["collectors", "instances"],
    queryFn: () => CollectorsService.listInstances(),
    refetchInterval: isEnabled ? interval : false,
  })
}

export const useCollectorPlugins = () => {
  return useQuery({
    queryKey: ["collectors", "plugins"],
    queryFn: () => CollectorsService.listPlugins(),
  })
}

export const useCollectorStats = (id: number, range: string = "24h") => {
  const { isEnabled, interval } = useAutoRefresh()
  return useQuery({
    queryKey: ["collectors", id, "stats", range],
    queryFn: () => CollectorsService.getStats({ id, range }),
    enabled: !!id,
    refetchInterval: isEnabled ? interval : false,
  })
}

export const useCreateCollector = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: CollectorsCreateInstanceData) =>
      CollectorsService.createInstance(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["collectors", "instances"] })
    },
  })
}

export const useUpdateCollector = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: CollectorsUpdateInstanceData) =>
      CollectorsService.updateInstance(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["collectors", "instances"] })
    },
  })
}

export const useToggleCollector = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: CollectorsToggleInstanceData) =>
      CollectorsService.toggleInstance(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["collectors", "instances"] })
    },
  })
}

export const useTriggerCollector = () => {
  return useMutation({
    mutationFn: (data: CollectorsTriggerInstanceData) =>
      CollectorsService.triggerInstance(data),
  })
}

/**
 * Fetch volume statistics (items collected per ledger by hour)
 * Endpoint: GET /api/v1/collectors/stats/volume?range=24h
 */
export const useCollectorVolume = (range: string = "24h") => {
  const { isEnabled, interval } = useAutoRefresh()
  return useQuery({
    queryKey: ["collectors", "stats", "volume", range],
    queryFn: async (): Promise<VolumeDataPoint[]> => {
      const response = await fetch(
        `/api/v1/collectors/stats/volume?range=${encodeURIComponent(range)}`,
      )
      if (!response.ok) {
        throw new Error(`Failed to fetch volume stats: ${response.statusText}`)
      }
      return response.json()
    },
    select: (data) => data.map(({ Exchange, ...rest }) => rest),
    refetchInterval: isEnabled ? interval : false,
    staleTime: 30000, // 30s
  })
}

/**
 * Fetch exchange health status
 * Determines traffic light status based on recent exchange collector runs
 */
export const useExchangeHealth = () => {
  const { isEnabled, interval } = useAutoRefresh()
  return useQuery({
    queryKey: ["collectors", "exchange-health"],
    queryFn: async (): Promise<ExchangeHealthInfo> => {
      const response = await fetch(`/api/v1/collectors/stats/activity`)
      if (!response.ok) throw new Error("Failed to fetch exchange health")
      const logs = await response.json()
      const now = new Date()
      const dayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000)
      const exchangeRuns = logs.filter((log: any) => {
        const name = (log.collector ?? log.collector_name ?? "").toLowerCase()
        return name.includes("coinspot") || name.includes("exchange")
      })
      const recentRuns = exchangeRuns.filter(
        (r: any) => new Date(r.timestamp) >= dayAgo,
      )
      const failedRecent = recentRuns.filter(
        (r: any) => r.status === "error" || r.status === "failed",
      )

      let status: ExchangeHealthStatus = "unknown"
      let details = "No exchange collector data available"
      if (recentRuns.length === 0) {
        status = "unknown"
      } else if (
        recentRuns[0].status === "error" ||
        recentRuns[0].status === "failed"
      ) {
        status = "red"
        details = `Last run failed at ${recentRuns[0].timestamp}`
      } else if (failedRecent.length > 0) {
        status = "amber"
        details = `${failedRecent.length} failed run(s) in last 24h`
      } else {
        status = "green"
        details = `All ${recentRuns.length} runs successful in last 24h`
      }
      return {
        status,
        lastRunStatus: recentRuns[0]?.status ?? null,
        lastRunAt: recentRuns[0]?.timestamp ?? null,
        failedCount24h: failedRecent.length,
        totalCount24h: recentRuns.length,
        details,
      }
    },
    refetchInterval: isEnabled ? interval : false,
    staleTime: 30000,
  })
}

/**
 * Fetch aggregate statistics for all collectors
 * Endpoint: GET /api/v1/collectors/stats/summary
 */
export const useCollectorSummaryStats = () => {
  const { isEnabled, interval } = useAutoRefresh()
  return useQuery({
    queryKey: ["collectors", "stats", "summary"],
    queryFn: async (): Promise<AggregateStats[]> => {
      const response = await fetch(`/api/v1/collectors/stats/summary`)
      if (!response.ok) {
        throw new Error(`Failed to fetch summary stats: ${response.statusText}`)
      }
      return response.json()
    },
    refetchInterval: isEnabled ? interval : false,
    staleTime: 30000, // 30s
  })
}
