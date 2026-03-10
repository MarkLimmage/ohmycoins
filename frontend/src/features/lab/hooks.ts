import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { AgentService, OpenAPI, UsersService } from "@/client"

export const useLabSessions = (skip = 0, limit = 50) => {
  return useQuery({
    queryKey: ["lab-sessions", skip, limit],
    queryFn: () => AgentService.listAgentSessions({ skip, limit }),
    staleTime: 10_000,
    refetchInterval: 15_000,
  })
}

export const useLabSession = (sessionId: string | null) => {
  return useQuery({
    queryKey: ["lab-session", sessionId],
    queryFn: () => AgentService.getAgentSession({ sessionId: sessionId! }),
    enabled: !!sessionId,
    staleTime: 5_000,
    refetchInterval: 10_000,
  })
}

export const useCreateSession = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: { user_goal: string; llm_credential_id?: string }) =>
      AgentService.createAgentSession({
        requestBody: data,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["lab-sessions"] })
    },
  })
}

export const useCancelSession = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (sessionId: string) =>
      AgentService.cancelAgentSession({ sessionId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["lab-sessions"] })
    },
  })
}

export const useDeleteSession = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (sessionId: string) =>
      AgentService.deleteAgentSession({ sessionId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["lab-sessions"] })
    },
  })
}

export const useLlmCredentials = () => {
  return useQuery({
    queryKey: ["llm-credentials"],
    queryFn: () => UsersService.listLlmCredentials(),
    staleTime: 60_000,
  })
}

export const useSessionArtifacts = (sessionId: string | null) => {
  return useQuery({
    queryKey: ["session-artifacts", sessionId],
    queryFn: () => AgentService.getSessionArtifacts({ sessionId: sessionId! }),
    enabled: !!sessionId,
    staleTime: 10_000,
    refetchInterval: 15_000,
  })
}

export const usePromoteArtifact = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (data: {
      artifactId: string
      algorithmName: string
      description: string
      positionLimit: number
      dailyLossLimit: number
      executionFrequency: number
    }) => {
      const rawToken = OpenAPI.TOKEN
      const token =
        typeof rawToken === "function"
          ? await (rawToken as () => Promise<string>)()
          : rawToken

      const response = await fetch(
        `${OpenAPI.BASE}/api/v1/lab/agent/artifacts/${data.artifactId}/promote`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          body: JSON.stringify({
            algorithm_name: data.algorithmName,
            description: data.description,
            position_limit: data.positionLimit,
            daily_loss_limit: data.dailyLossLimit,
            execution_frequency: data.executionFrequency,
          }),
        },
      )
      if (!response.ok) throw new Error("Failed to promote artifact")
      return response.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["session-artifacts"] })
    },
  })
}

export const useModelInfo = (artifactId: string | null) => {
  return useQuery({
    queryKey: ["model-info", artifactId],
    queryFn: async () => {
      const rawToken = OpenAPI.TOKEN
      const token =
        typeof rawToken === "function"
          ? await (rawToken as () => Promise<string>)()
          : rawToken
      const response = await fetch(
        `${OpenAPI.BASE}/api/v1/lab/agent/artifacts/${artifactId}/info`,
        {
          headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}) },
        },
      )
      if (!response.ok) throw new Error("Failed to fetch model info")
      return response.json() as Promise<{
        artifact_id: string
        model_type: string
        task_type: string
        feature_columns: string[]
        training_metrics: Record<string, number> | null
      }>
    },
    enabled: !!artifactId,
  })
}

export const useModelPredict = () => {
  return useMutation({
    mutationFn: async (data: {
      artifactId: string
      featureValues: Record<string, number>
    }) => {
      const rawToken = OpenAPI.TOKEN
      const token =
        typeof rawToken === "function"
          ? await (rawToken as () => Promise<string>)()
          : rawToken
      const response = await fetch(
        `${OpenAPI.BASE}/api/v1/lab/agent/artifacts/${data.artifactId}/predict`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          body: JSON.stringify({ feature_values: data.featureValues }),
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
      }>
    },
  })
}
