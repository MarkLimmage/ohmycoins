import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { CollectorsService } from "@/client"
import { CollectorPlugin, CollectorInstance, CollectorCreate, CollectorStatus, CollectorStats } from "./types"

// Adapter function to convert API Collector to Frontend CollectorInstance
const mapApiCollectorToInstance = (apiCollector: any): CollectorInstance => {
  return {
    id: String(apiCollector.id),
    name: apiCollector.name,
    plugin_id: apiCollector.plugin_name, // Map backend 'plugin_name' to frontend 'plugin_id'
    status: (apiCollector.is_enabled ? "running" : "idle"), // Derive status from is_enabled for now
    config: apiCollector.config || {},
    last_run: apiCollector.last_run_at || null,
    next_run: null, // Not provided by API yet
    is_active: apiCollector.is_enabled,
    error_count: 0, // Not provided by API yet
    success_count: 0, // Not provided by API yet
  }
}

// Mock collector stats until Track A is ready
const mockCollectorStats = (collectorId: string): CollectorStats => {
  const now = new Date();
  const throughput = Array.from({ length: 60 }, (_, i) => ({
    // Last hour of data points (every minute)
    timestamp: new Date(now.getTime() - (59 - i) * 60000).toISOString(),
    // Random throughput between 0 and 100 items
    items_collected: Math.floor(Math.random() * 100)
  }));
  
  return {
    collector_id: collectorId,
    throughput,
    status: Math.random() > 0.9 ? 'failed' : 'success', // Mostly successful
    last_success: new Date(now.getTime() - Math.floor(Math.random() * 300000)).toISOString() // Random time in last 5 mins
  };
};

export const useCollectorStats = (collectorId: string) => {
  return useQuery({
    queryKey: ['collector-stats', collectorId],
    queryFn: async (): Promise<CollectorStats> => {
      // Simulate network delay
      await new Promise(resolve => setTimeout(resolve, 500));
      return mockCollectorStats(collectorId);
    },
    // Poll every 5 seconds to update stats
    refetchInterval: 5000,
    // Keep previous data while fetching new data to avoid flickering
    placeholderData: (previousData) => previousData
  });
};

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

