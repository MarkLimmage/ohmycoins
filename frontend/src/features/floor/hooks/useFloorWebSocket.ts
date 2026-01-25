import { useState, useEffect, useRef, useCallback } from "react"
import { OpenAPI } from "@/client" // Assuming client setup
import type { PLTickerData, AlgorithmData } from "../types"

// Mock initial data to prevent crashes while loading
const INITIAL_TICKER: PLTickerData = {
  total_pnl: 0,
  pnl_percentage: 0,
  active_count: 0,
  paused_count: 0,
  is_connected: false,
  last_update: new Date().toISOString(),
}

export const useFloorWebSocket = () => {
  const [tickerData, setTickerData] = useState<PLTickerData>(INITIAL_TICKER)
  const [algorithms, setAlgorithms] = useState<AlgorithmData[]>([])
  const [isConnected, setIsConnected] = useState(false)
  const ws = useRef<WebSocket | null>(null)
  const reconnectTimeout = useRef<NodeJS.Timeout>(null)
  const pollInterval = useRef<NodeJS.Timeout>(null)

  const connect = useCallback(async () => {
    if (ws.current?.readyState === WebSocket.OPEN) return

    const token = await OpenAPI.TOKEN()
    // Replace http/https with ws/wss
    const baseUrl = OpenAPI.BASE?.replace(/^http/, "ws") || "wss://api.ohmycoins.com"
    const wsUrl = `${baseUrl}/ws/floor/pnl?token=${token}`

    try {
        const socket = new WebSocket(wsUrl)
        
        socket.onopen = () => {
            setIsConnected(true)
            setTickerData(prev => ({ ...prev, is_connected: true }))
            if (reconnectTimeout.current) clearTimeout(reconnectTimeout.current)
            if (pollInterval.current) clearInterval(pollInterval.current)
        }

        socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data)
                if (data.type === 'ticker') {
                    setTickerData({ ...data.payload, is_connected: true })
                } else if (data.type === 'algorithms') {
                    setAlgorithms(data.payload)
                }
            } catch (e) {
                console.error("WS Parse Error", e)
            }
        }

        socket.onclose = () => {
            setIsConnected(false)
            setTickerData(prev => ({ ...prev, is_connected: false }))
            // Attempt reconnect in 2s
            reconnectTimeout.current = setTimeout(connect, 2000)
            // Start polling as fallback
            startPolling()
        }

        socket.onerror = (err) => {
            console.error("WS Error", err)
            socket.close()
        }

        ws.current = socket
    } catch (err) {
        console.error("WS Connection Error", err)
        reconnectTimeout.current = setTimeout(connect, 2000)
        startPolling()
    }
  }, [])

  const startPolling = useCallback(() => {
     if (pollInterval.current) return
     
     pollInterval.current = setInterval(async () => {
         try {
             // Mock polling fetch if WS fails
             // In real app: const res = await fetch(...)
             // For now we just keep state
         } catch (e) {
             console.error("Polling error", e)
         }
     }, 2000)
  }, [])

  useEffect(() => {
    connect()

    return () => {
      ws.current?.close()
      if (reconnectTimeout.current) clearTimeout(reconnectTimeout.current)
      if (pollInterval.current) clearInterval(pollInterval.current)
    }
  }, [connect])

  return { tickerData, algorithms, isConnected }
}
