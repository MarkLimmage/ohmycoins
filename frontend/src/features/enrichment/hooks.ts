import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { EnrichmentService } from "@/client"
import type {
  EnrichmentRunsResponse,
  EnrichmentStats,
  TriggerEnrichmentResponse,
} from "./types"

export const useEnrichmentStats = () => {
  return useQuery({
    queryKey: ["enrichment-stats"],
    queryFn: async () => {
      const response = await EnrichmentService.getEnrichmentStats()
      return response as unknown as EnrichmentStats
    },
    staleTime: 30_000,
    refetchInterval: 60_000,
  })
}

export const useEnrichmentRuns = (limit = 50) => {
  return useQuery({
    queryKey: ["enrichment-runs", limit],
    queryFn: async () => {
      const response = await EnrichmentService.getEnrichmentRuns({ limit })
      return response as unknown as EnrichmentRunsResponse
    },
    staleTime: 15_000,
    refetchInterval: 30_000,
  })
}

export const useTriggerEnrichment = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({
      enricher = "all",
      limit = 100,
    }: {
      enricher?: string
      limit?: number
    }) => {
      const response = await EnrichmentService.triggerEnrichment({
        enricher,
        limit,
      })
      return response as unknown as TriggerEnrichmentResponse
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["enrichment-stats"] })
      queryClient.invalidateQueries({ queryKey: ["enrichment-runs"] })
    },
  })
}
