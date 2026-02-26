import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useMemo } from "react"
import { CollectorsService } from "@/client"
import { useCollectorSummaryStats } from "@/hooks/useCollectors"
import type {
  CollectorCardData,
  CollectorCreate,
  CollectorInstance,
  CollectorPlugin,
  CollectorStatsPoint,
  CollectorStatus,
} from "./types"

// Adapter function to convert API Collector to Frontend CollectorInstance
const mapApiCollectorToInstance = (apiCollector: any): CollectorInstance => {
  return {
    id: String(apiCollector.id),
    name: apiCollector.name,
    plugin_id: apiCollector.plugin_name, // Map backend 'plugin_name' to frontend 'plugin_id'
    status: (apiCollector.status as CollectorStatus) || "idle",
    config: apiCollector.config || {},
    schedule_cron: apiCollector.schedule_cron || "*/15 * * * *", // Default to 15m if missing
    last_run: apiCollector.last_run_at || null,
    next_run: null, // Not provided by API yet
    is_active: apiCollector.is_enabled,
    error_count: 0, // Not provided by API yet
    success_count: 0, // Not provided by API yet
  }
}

export const useCollectors = () => {
  const queryClient = useQueryClient()

  // Fetch Plugins
  const pluginsQuery = useQuery({
    queryKey: ["collector-plugins"],
    queryFn: async () => {
      const response = await CollectorsService.listPlugins()
      return response as unknown as CollectorPlugin[]
    },
  })

  // Fetch Instances
  const instancesQuery = useQuery({
    queryKey: ["collector-instances"],
    queryFn: async () => {
      const response = await CollectorsService.listInstances()
      const data = response as any[] // As list of dict/model
      return data.map(mapApiCollectorToInstance)
    },
    // Poll every 5 seconds to get status updates
    refetchInterval: 5000,
  })

  // Create Instance
  const createMutation = useMutation({
    mutationFn: async (data: CollectorCreate) => {
      console.log("Creating collector with data: ", data)
      return await CollectorsService.createInstance({
        requestBody: {
          name: data.name,
          plugin_name: data.plugin_id,
          config: data.config,
          is_enabled: data.is_active ?? false,
          schedule_cron: data.schedule_cron,
        },
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["collector-instances"] })
    },
  })

  // Update Instance
  const updateMutation = useMutation({
    mutationFn: async ({
      id,
      data,
    }: {
      id: string
      data: Partial<CollectorCreate>
    }) => {
      // The API requires name, but we might only be updating config.
      // However, CollectorForm always sends the full object.
      // If we support partial updates in the future, we need to handle this.
      // For now, defaulting to empty string if undefined (though it should be present from form)
      return await CollectorsService.updateInstance({
        id: Number(id),
        requestBody: {
          name: data.name!,
          plugin_name: data.plugin_id!,
          config: data.config,
          is_enabled: data.is_active,
          schedule_cron: data.schedule_cron,
        },
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["collector-instances"] })
    },
  })

  // Delete Instance
  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      return await CollectorsService.deleteInstance({
        id: Number(id),
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["collector-instances"] })
    },
  })

  // Toggle Instance
  const toggleMutation = useMutation({
    mutationFn: async ({ id }: { id: string; is_active?: boolean }) => {
      return await CollectorsService.toggleInstance({
        id: Number(id),
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["collector-instances"] })
    },
  })

  // Trigger Instance (Run Now)
  const runMutation = useMutation({
    mutationFn: async (id: string) => {
      return await CollectorsService.triggerInstance({
        id: Number(id),
      })
    },
    onSuccess: () => {
      // We might want to show a toast here
      console.log("Collector triggered successfully")
    },
  })

  return {
    plugins: pluginsQuery,
    instances: instancesQuery,
    createInstance: createMutation,
    updateInstance: updateMutation,
    deleteInstance: deleteMutation,
    toggleInstance: toggleMutation,
    runCollector: runMutation,
  }
}

export const useCollectorStats = (id: string, enabled = true) => {
  return useQuery({
    queryKey: ["collector-stats", id],
    queryFn: async (): Promise<CollectorStatsPoint[]> => {
      const response = await CollectorsService.getStats({
        id: Number(id),
        range: "24h",
      })
      return (response as any[]).map((r: any) => ({
        timestamp: r.timestamp,
        count: r.count ?? 0,
      }))
    },
    enabled: enabled && !!id,
    staleTime: 60000,
  })
}

export const usePluginCardData = () => {
  const { plugins, instances } = useCollectors()
  const { data: summaryStats } = useCollectorSummaryStats()

  const cards = useMemo((): CollectorCardData[] => {
    if (!plugins.data) return []
    return plugins.data.map((plugin) => {
      const instance = instances.data?.find(
        (inst) => inst.plugin_id === plugin.id,
      )
      const stats = summaryStats?.find(
        (s) => s.collector_name === instance?.name,
      )
      return {
        plugin_id: plugin.id,
        plugin_name: plugin.name,
        plugin_description: plugin.description,
        plugin_schema: plugin.schema,
        instance_id: instance?.id ?? null,
        instance_name: instance?.name ?? null,
        status: instance?.status ?? "idle",
        config: instance?.config ?? {},
        schedule_cron: instance?.schedule_cron ?? "*/15 * * * *",
        last_run: instance?.last_run ?? null,
        is_active: instance?.is_active ?? false,
        success_rate: stats?.uptime_pct ?? null,
        total_records: stats?.total_records ?? null,
        avg_duration: stats?.avg_duration_seconds ?? null,
        total_runs: stats?.total_runs ?? null,
      }
    })
  }, [plugins.data, instances.data, summaryStats])

  return {
    cards,
    isLoading: plugins.isLoading || instances.isLoading,
    error: plugins.error || instances.error,
  }
}

export const useCreateAndEnable = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (plugin: CollectorPlugin) => {
      return await CollectorsService.createInstance({
        requestBody: {
          name: plugin.id,
          plugin_name: plugin.id,
          config: {},
          is_enabled: true,
          schedule_cron: "*/15 * * * *",
        },
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["collector-instances"] })
      queryClient.invalidateQueries({ queryKey: ["collectors", "instances"] })
    },
  })
}
