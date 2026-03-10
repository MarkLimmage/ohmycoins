import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import type { BacktestRunCreate } from "@/client"
import { BacktestsService } from "@/client"

export const useRunBacktest = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: BacktestRunCreate) =>
      BacktestsService.createBacktest({ requestBody: data }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["backtests"] })
    },
  })
}

export const useBacktestResults = (id: string | null) => {
  return useQuery({
    queryKey: ["backtest", id],
    queryFn: () => BacktestsService.getBacktest({ backtestId: id! }),
    enabled: !!id,
    staleTime: 5_000,
  })
}

export const useBacktestList = () => {
  return useQuery({
    queryKey: ["backtests"],
    queryFn: () => BacktestsService.listBacktests({ limit: 50 }),
    staleTime: 10_000,
    refetchInterval: (query) => {
      const data = query.state.data
      if (
        data?.data?.some(
          (b) => b.status === "running" || b.status === "pending",
        )
      ) {
        return 5_000
      }
      return false
    },
  })
}
