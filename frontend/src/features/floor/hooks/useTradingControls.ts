import axios from "axios"
import { useCallback } from "react"
import { OpenAPI } from "@/client"

export const useTradingControls = () => {
  const getHeaders = useCallback(async () => {
    const token = OpenAPI.TOKEN
    return { Authorization: `Bearer ${token}` }
  }, [])

  const pauseAlgorithm = useCallback(
    async (id: string) => {
      const headers = await getHeaders()
      await axios.post(
        `${OpenAPI.BASE}/api/v1/floor/algorithms/${id}/pause`,
        {},
        { headers },
      )
    },
    [getHeaders],
  )

  const resumeAlgorithm = useCallback(
    async (id: string) => {
      const headers = await getHeaders()
      await axios.post(
        `${OpenAPI.BASE}/api/v1/floor/algorithms/${id}/resume`,
        {},
        { headers },
      )
    },
    [getHeaders],
  )

  const stopAlgorithm = useCallback(
    async (id: string) => {
      const headers = await getHeaders()
      await axios.post(
        `${OpenAPI.BASE}/api/v1/floor/algorithms/${id}/stop`,
        {},
        { headers },
      )
    },
    [getHeaders],
  )

  const emergencyStop = useCallback(async () => {
    const headers = await getHeaders()
    await axios.post(
      `${OpenAPI.BASE}/api/v1/floor/emergency-stop`,
      {},
      { headers },
    )
  }, [getHeaders])

  return {
    pauseAlgorithm,
    resumeAlgorithm,
    stopAlgorithm,
    emergencyStop,
  }
}
