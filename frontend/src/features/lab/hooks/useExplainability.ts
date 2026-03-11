import { useMutation, useQuery } from "@tanstack/react-query"
import { OpenAPI } from "@/client"

async function resolveToken(): Promise<string | undefined> {
  const rawToken = OpenAPI.TOKEN
  const token =
    typeof rawToken === "function"
      ? await (rawToken as () => Promise<string>)()
      : rawToken
  return token ?? undefined
}

export const useExplainModel = () => {
  return useMutation({
    mutationFn: async (artifactId: string) => {
      const token = await resolveToken()
      const response = await fetch(
        `${OpenAPI.BASE}/api/v1/lab/agent/artifacts/${artifactId}/explain`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
        },
      )
      if (!response.ok) throw new Error("Failed to explain model")
      return response.json() as Promise<{
        supported: boolean
        reason: string | null
        feature_importance:
          | { feature_name: string; importance: number }[]
          | null
        plot_path: string | null
        model_type: string
        shap_base_value: number | null
        cached: boolean
      }>
    },
  })
}

export const useExplanation = (artifactId: string | null) => {
  return useQuery({
    queryKey: ["explanation", artifactId],
    queryFn: async () => {
      const token = await resolveToken()
      const response = await fetch(
        `${OpenAPI.BASE}/api/v1/lab/agent/artifacts/${artifactId}/explain`,
        {
          headers: {
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
        },
      )
      if (!response.ok) return null
      return response.json() as Promise<{
        supported: boolean
        reason: string | null
        feature_importance:
          | { feature_name: string; importance: number }[]
          | null
        plot_path: string | null
        model_type: string
        shap_base_value: number | null
        cached: boolean
      }>
    },
    enabled: !!artifactId,
    staleTime: 60_000,
  })
}

export const useModelPredict = () => {
  return useMutation({
    mutationFn: async (data: {
      artifactId: string
      featureValues: Record<string, number>
      includeExplanation?: boolean
    }) => {
      const token = await resolveToken()
      const response = await fetch(
        `${OpenAPI.BASE}/api/v1/lab/agent/artifacts/${data.artifactId}/predict`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          body: JSON.stringify({
            feature_values: data.featureValues,
            include_explanation: data.includeExplanation ?? false,
          }),
        },
      )
      if (!response.ok) throw new Error("Failed to predict")
      return response.json() as Promise<{
        prediction: number | string
        prediction_label: string | null
        probabilities: Record<string, number> | null
        model_type: string
        task_type: string
        feature_columns_used: string[]
        shap_values?: Record<string, number>
        shap_base_value?: number
      }>
    },
  })
}
