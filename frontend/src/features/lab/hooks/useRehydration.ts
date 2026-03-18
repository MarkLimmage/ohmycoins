import { useCallback, useState } from "react"
import { OpenAPI } from "@/client"
import type { LabEvent } from "../types"

interface RehydrationResponse {
  session_id: string
  last_sequence_id: number
  event_ledger: LabEvent[]
}

async function resolveToken(): Promise<string | undefined> {
  const rawToken = OpenAPI.TOKEN
  if (typeof rawToken === "function") {
    return await (rawToken as () => Promise<string>)()
  }
  return rawToken
}

export const useRehydration = () => {
  const [isRehydrating, setIsRehydrating] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const rehydrate = useCallback(async (sessionId: string) => {
    setIsRehydrating(true)
    setError(null)
    try {
      const token = await resolveToken()
      const headers: Record<string, string> = {}
      if (token) {
        headers.Authorization = `Bearer ${token}`
      }
      const response = await fetch(
        `/api/v1/lab/agent/sessions/${sessionId}/rehydrate`,
        { headers },
      )
      if (!response.ok) {
        throw new Error(`Rehydration failed: ${response.statusText}`)
      }
      const data: RehydrationResponse = await response.json()
      return data
    } catch (err) {
      setError(err as Error)
      return null
    } finally {
      setIsRehydrating(false)
    }
  }, [])

  return { rehydrate, isRehydrating, error }
}
