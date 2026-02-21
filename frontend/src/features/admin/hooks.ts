import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { CollectorsService } from "@/client"
import { CollectorPlugin, CollectorInstance, CollectorCreate, CollectorStatus } from "./types"

// Adapter function to convert API Collector to Frontend CollectorInstance
const mapApiCollectorToInstance = (apiCollector: any): CollectorInstance => {
  return {
    id: String(apiCollector.id),
    name: apiCollector.name,
    plugin_id: apiCollector.plugin_name, // Map backend 'plugin_name' to frontend 'plugin_id'
    status: (apiCollector.status as CollectorStatus) || "idle",
    config: apiCollector.config || {},
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
          schedule_cron: "*/15 * * * *"
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
      return await CollectorsService.updateInstance({
        id: Number(id),
        requestBody: {
          name: data.name,
          config: data.config,
          is_enabled: data.is_active,
          // plugin_name is likely not editable, check backend model
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
    mutationFn: async ({ id, is_active }: { id: string; is_active: boolean }) => {
      return await CollectorsService.toggleInstance({
        id: Number(id)
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["collector-instances"] })
    }
  })

  return {
    plugins: pluginsQuery,
    instances: instancesQuery,
    createInstance: createMutation,
    deleteInstance: deleteMutation,
    toggleInstance: toggleMutation
  }
}

