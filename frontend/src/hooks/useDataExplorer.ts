import { useQuery } from "@tanstack/react-query"

export interface PriceDataPoint {
  timestamp: string
  coin_type: string
  price: number
}

export interface PriceDataResponse {
  data: PriceDataPoint[]
  total_points: number
}

/**
 * Fetch price data for a specific coin within a date range
 */
export const usePriceData = (
  coinType: string | null,
  startDate: string | null,
  endDate: string | null,
) => {
  return useQuery({
    queryKey: ["price-data", coinType, startDate, endDate],
    queryFn: async (): Promise<PriceDataResponse> => {
      if (!coinType || !startDate || !endDate) {
        return { data: [], total_points: 0 }
      }

      const params = new URLSearchParams()
      params.append("coin_type", coinType)
      params.append("start_date", `${startDate}T00:00:00Z`)
      params.append("end_date", `${endDate}T23:59:59Z`)
      params.append("limit", "500")

      const response = await fetch(
        `/api/v1/utils/price-data/?${params.toString()}`,
      )
      if (!response.ok) {
        throw new Error(`Failed to fetch price data: ${response.statusText}`)
      }
      return response.json()
    },
    enabled: !!coinType && !!startDate && !!endDate,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

/**
 * Fetch all coins available in the price data
 */
export const useAvailableCoins = () => {
  return useQuery({
    queryKey: ["available-coins"],
    queryFn: async (): Promise<string[]> => {
      const response = await fetch("/api/v1/utils/available-coins/")
      if (!response.ok) {
        // Return common coins if endpoint doesn't exist
        return ["BTC", "ETH", "DOGE", "ADA", "XRP", "SOL"]
      }
      return response.json()
    },
    staleTime: 60 * 60 * 1000, // 1 hour
  })
}

/**
 * Transform price data for LineChart (single coin, multiple timestamps)
 */
export const transformPriceDataForLineChart = (
  priceData: PriceDataPoint[],
): Array<{ time: string; [key: string]: number | string }> => {
  return priceData.map((point) => ({
    time: new Date(point.timestamp).toLocaleString(),
    [point.coin_type]: point.price,
  }))
}

/**
 * Transform price data for BarChart (multiple coins, single timestamp range)
 * Shows latest price for each coin
 */
export const transformPriceDataForBarChart = (
  priceData: PriceDataPoint[],
): Array<{ coin: string; price: number }> => {
  if (priceData.length === 0) return []

  // Get the latest timestamp
  const latestTimestamp = Math.max(
    ...priceData.map((p) => new Date(p.timestamp).getTime()),
  )

  // Filter data to latest timestamp and aggregate by coin
  return priceData
    .filter((p) => new Date(p.timestamp).getTime() === latestTimestamp)
    .map((p) => ({
      coin: p.coin_type,
      price: p.price,
    }))
}
