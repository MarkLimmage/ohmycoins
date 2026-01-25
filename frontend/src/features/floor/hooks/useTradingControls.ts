import { useCallback } from "react"
import { OpenAPI } from "@/client"
import axios from "axios"

export const useTradingControls = () => {
  const getHeaders = async () => {
      const token = OpenAPI.TOKEN
      return { Authorization: `Bearer ${token}` }
  }

  const pauseAlgorithm = useCallback(async (id: string) => {
    const headers = await getHeaders()
    await axios.post(`${OpenAPI.BASE}/api/v1/floor/algorithms/${id}/pause`, {}, { headers })
  }, [])

  const resumeAlgorithm = useCallback(async (id: string) => {
    const headers = await getHeaders()
    await axios.post(`${OpenAPI.BASE}/api/v1/floor/algorithms/${id}/resume`, {}, { headers })
  }, [])

  const stopAlgorithm = useCallback(async (id: string) => {
    const headers = await getHeaders()
    await axios.post(`${OpenAPI.BASE}/api/v1/floor/algorithms/${id}/stop`, {}, { headers })
  }, [])

  const emergencyStop = useCallback(async () => {
    const headers = await getHeaders()
    await axios.post(`${OpenAPI.BASE}/api/v1/floor/emergency-stop`, {}, { headers })
  }, [])

  return {
    pauseAlgorithm,
    resumeAlgorithm,
    stopAlgorithm,
    emergencyStop,
  }
}
