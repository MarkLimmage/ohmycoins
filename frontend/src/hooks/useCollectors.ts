import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { CollectorsService } from "../client/sdk.gen"
import type { CollectorsCreateInstanceData, CollectorsUpdateInstanceData, CollectorsToggleInstanceData, CollectorsTriggerInstanceData } from "../client/types.gen"
import { useAutoRefresh } from "../context/AutoRefreshContext"

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
        mutationFn: (data: CollectorsCreateInstanceData) => CollectorsService.createInstance(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["collectors", "instances"] })
        },
    })
}

export const useUpdateCollector = () => {
    const queryClient = useQueryClient()
    return useMutation({
        mutationFn: (data: CollectorsUpdateInstanceData) => CollectorsService.updateInstance(data),
        onSuccess: () => {
             queryClient.invalidateQueries({ queryKey: ["collectors", "instances"] })
        },
    })
}

export const useToggleCollector = () => {
    const queryClient = useQueryClient()
    return useMutation({
        mutationFn: (data: CollectorsToggleInstanceData) => CollectorsService.toggleInstance(data),
        onSuccess: () => {
             queryClient.invalidateQueries({ queryKey: ["collectors", "instances"] })
        },
    })
}

export const useTriggerCollector = () => {
    return useMutation({
        mutationFn: (data: CollectorsTriggerInstanceData) => CollectorsService.triggerInstance(data),
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
                `/api/v1/collectors/stats/volume?range=${encodeURIComponent(range)}`
            )
            if (!response.ok) {
                throw new Error(`Failed to fetch volume stats: ${response.statusText}`)
            }
            return response.json()
        },
        refetchInterval: isEnabled ? interval : false,
        staleTime: 30000, // 30s
    })
}

/**
 * Fetch activity logs (recent collector runs)
 * Endpoint: GET /api/v1/collectors/stats/activity?limit=50
 */
export const useCollectorActivity = (limit: number = 50) => {
    const { isEnabled, interval } = useAutoRefresh()
    return useQuery({
        queryKey: ["collectors", "stats", "activity", limit],
        queryFn: async (): Promise<ActivityLog[]> => {
            const response = await fetch(
                `/api/v1/collectors/stats/activity?limit=${limit}`
            )
            if (!response.ok) {
                throw new Error(`Failed to fetch activity logs: ${response.statusText}`)
            }
            return response.json()
        },
        refetchInterval: isEnabled ? interval : false,
        staleTime: 30000, // 30s
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
            const response = await fetch(
                `/api/v1/collectors/stats/summary`
            )
            if (!response.ok) {
                throw new Error(`Failed to fetch summary stats: ${response.statusText}`)
            }
            return response.json()
        },
        refetchInterval: isEnabled ? interval : false,
        staleTime: 30000, // 30s
    })
}
