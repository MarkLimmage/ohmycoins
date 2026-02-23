import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { CollectorsService } from "../client/sdk.gen"
import type { CollectorsCreateInstanceData, CollectorsUpdateInstanceData, CollectorsToggleInstanceData, CollectorsTriggerInstanceData, CollectorsGetStatsData } from "../client/types.gen"
import { useAutoRefresh } from "../context/AutoRefreshContext"

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
