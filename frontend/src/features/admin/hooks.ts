import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { CollectorsService } from "@/client"
import { CollectorPlugin, CollectorInstance, CollectorCreate, CollectorStatus, CollectorStatsPoint } from "./types"

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
    }
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
    refetchInterval: 5000 
  })

  // Create Instance
  const createMutation = useMutation({
    mutationFn: async (data: CollectorCreate) => {
      console.log("Creating collector with data: ", data);
      return await CollectorsService.createInstance({
        requestBody: {
          name: data.name,
          plugin_name: data.plugin_id,
          config: data.config,
          is_enabled: data.is_active ?? false,
          schedule_cron: data.schedule_cron
        }
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["collector-instances"] })
    }
  })

  // Update Instance
  const updateMutation = useMutation({
    mutationFn: async ({ id, data }: { id: string, data: Partial<CollectorCreate> }) => {
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
          schedule_cron: data.schedule_cron
        }
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["collector-instances"] })
    }
  })

  // Delete Instance
  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      return await CollectorsService.deleteInstance({
        id: Number(id)
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["collector-instances"] })
    }
  })

  // Toggle Instance
  const toggleMutation = useMutation({
      mutationFn: async ({ id, is_active }: { id: string, is_active: boolean }) => {
          return await CollectorsService.toggleInstance({
              id: Number(id)
          })
      },
      onSuccess: () => {
          queryClient.invalidateQueries({ queryKey: ["collector-instances"] })
      }
  })

  // Trigger Instance (Run Now)
  const runMutation = useMutation({
      mutationFn: async (id: string) => {
          return await CollectorsService.triggerInstance({
              id: Number(id)
          })
      },
      onSuccess: () => {
        // We might want to show a toast here
        console.log("Collector triggered successfully")
      }
  })

  return {
    plugins: pluginsQuery,
    instances: instancesQuery,
    createInstance: createMutation,
    updateInstance: updateMutation,
    deleteInstance: deleteMutation,
    toggleInstance: toggleMutation,
    runCollector: runMutation
  }
}

export const useCollectorStats = (id: string, enabled = true) => {
  return useQuery({
    queryKey: ["collector-stats", id],
    queryFn: async (): Promise<CollectorStatsPoint[]> => {
      // Mock data: Generate 24h history
      const points: CollectorStatsPoint[] = [];
      const now = new Date();
      for (let i = 24; i >= 0; i--) {
        points.push({
          timestamp: new Date(now.getTime() - i * 3600000).toISOString(),
          count: Math.floor(Math.random() * 50) + 10 
        });
      }
      return points;
    },
    enabled: enabled,
    staleTime: 60000 // Cache for 1 min
  })
}

