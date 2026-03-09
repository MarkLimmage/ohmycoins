import { useCallback, useEffect, useRef, useState } from "react"
import { OpenAPI } from "@/client"
import type { AgentMessage } from "@/components/Lab/types"

interface UseLabWebSocketOptions {
  sessionId: string | null
  enabled?: boolean
}

interface UseLabWebSocketReturn {
  messages: AgentMessage[]
  isConnected: boolean
  isDone: boolean
  sessionStatus: string | null
}

export const useLabWebSocket = ({
  sessionId,
  enabled = true,
}: UseLabWebSocketOptions): UseLabWebSocketReturn => {
  const [messages, setMessages] = useState<AgentMessage[]>([])
  const [isConnected, setIsConnected] = useState(false)
  const [isDone, setIsDone] = useState(false)
  const [sessionStatus, setSessionStatus] = useState<string | null>(null)
  const ws = useRef<WebSocket | null>(null)
  const messageIds = useRef(new Set<string>())

  const connect = useCallback(async () => {
    if (!sessionId || !enabled) return

    let token: string | undefined
    const rawToken = OpenAPI.TOKEN
    if (typeof rawToken === "function") {
      try {
        token = await (rawToken as () => Promise<string>)()
      } catch (err) {
        console.error("Failed to resolve token:", err)
        return
      }
    } else {
      token = rawToken
    }

    const baseUrl =
      OpenAPI.BASE?.replace(/^http/, "ws") || "wss://api.ohmycoins.com"
    const wsUrl = `${baseUrl}/ws/agent/${sessionId}/stream?token=${token}`

    try {
      const socket = new WebSocket(wsUrl)

      socket.onopen = () => {
        setIsConnected(true)
      }

      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)

          // Handle status messages (done signals)
          if (data.type === "status" && data.done) {
            setSessionStatus(data.status || "completed")
            setIsDone(true)
            return
          }

          // Deduplicate by ID
          const msgId =
            data.id || `${Date.now()}-${Math.random().toString(36).slice(2)}`
          if (messageIds.current.has(msgId)) return
          messageIds.current.add(msgId)

          const newMessage: AgentMessage = {
            id: msgId,
            type: data.type || "output",
            content: data.content || "",
            timestamp: data.timestamp || new Date().toISOString(),
            metadata: data.metadata,
          }

          setMessages((prev) => [...prev, newMessage])
        } catch (error) {
          console.error("Failed to parse WS message:", error)
        }
      }

      socket.onclose = () => {
        setIsConnected(false)
      }

      socket.onerror = (error) => {
        console.error("Agent WS error:", error)
        setIsConnected(false)
      }

      ws.current = socket
    } catch (err) {
      console.error("Agent WS connection error:", err)
    }
  }, [sessionId, enabled])

  useEffect(() => {
    // Reset state on session change
    setMessages([])
    setIsDone(false)
    setSessionStatus(null)
    messageIds.current.clear()

    connect().catch((err) => {
      console.error("Connection error:", err)
    })

    return () => {
      if (ws.current?.readyState === WebSocket.OPEN) {
        ws.current.close()
      }
      ws.current = null
    }
  }, [connect])

  return { messages, isConnected, isDone, sessionStatus }
}
