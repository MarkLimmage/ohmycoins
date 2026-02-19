import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { CollectorPlugin, CollectorInstance, CollectorCreate } from "./types"

// Mock data
const MOCK_PLUGINS: CollectorPlugin[] = [
  {
    id: "coindesk_scraper",
    name: "CoinDesk News Scraper",
    description: "Scrapes latest crypto news from CoinDesk.",
    version: "1.0.0",
    schema: {
      type: "object",
      properties: {
        base_url: { type: "string", title: "Base URL", default: "https://www.coindesk.com" },
        max_articles: { type: "integer", title: "Max Articles", default: 10 },
        keywords: { 
          type: "array", 
          title: "Keywords", 
          items: { type: "string" },
          default: ["bitcoin", "ethereum"] 
        }
      },
      required: ["base_url"]
    }
  },
  {
    id: "yahoo_finance_price",
    name: "Yahoo Finance Price Collector",
    description: "Collects historical price data from Yahoo Finance.",
    version: "1.0.0",
    schema: {
      type: "object",
      properties: {
        symbols: { 
          type: "array", 
          title: "Symbols", 
          items: { type: "string" },
          default: ["BTC-USD", "ETH-USD"] 
        },
        interval: { 
          type: "string", 
          title: "Interval", 
          enum: ["1m", "5m", "15m", "1h", "1d"],
          default: "1h" 
        }
      },
      required: ["symbols", "interval"]
    }
  }
]

let MOCK_INSTANCES: CollectorInstance[] = [
  {
    id: "1",
    name: "CoinDesk Main",
    plugin_id: "coindesk_scraper",
    status: "idle",
    config: { base_url: "https://www.coindesk.com", max_articles: 10 },
    last_run: "2023-10-26T10:00:00Z",
    next_run: "2023-10-26T11:00:00Z",
    is_active: true,
    error_count: 0,
    success_count: 50
  }
]

// API Client Hook
export const useCollectors = () => {
  const queryClient = useQueryClient()

  const pluginsQuery = useQuery({
    queryKey: ["collector-plugins"],
    queryFn: async () => {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 500))
      return MOCK_PLUGINS
    }
  })

  const instancesQuery = useQuery({
    queryKey: ["collector-instances"],
    queryFn: async () => {
      await new Promise(resolve => setTimeout(resolve, 500))
      return MOCK_INSTANCES
    }
  })

  const createMutation = useMutation({
    mutationFn: async (data: CollectorCreate) => {
      await new Promise(resolve => setTimeout(resolve, 500))
      const newInstance: CollectorInstance = {
        id: Math.random().toString(36).substring(7),
        status: "idle",
        last_run: null,
        next_run: null,
        error_count: 0,
        success_count: 0,
        is_active: true,
        ...data
      }
      MOCK_INSTANCES = [...MOCK_INSTANCES, newInstance]
      return newInstance
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["collector-instances"] })
    }
  })

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
        await new Promise(resolve => setTimeout(resolve, 500))
        MOCK_INSTANCES = MOCK_INSTANCES.filter(i => i.id !== id)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["collector-instances"] })
    }
  })

  const toggleMutation = useMutation({
      mutationFn: async ({id, is_active}: {id: string, is_active: boolean}) => {
          await new Promise(resolve => setTimeout(resolve, 500))
          MOCK_INSTANCES = MOCK_INSTANCES.map(i => i.id === id ? {...i, is_active} : i)
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
