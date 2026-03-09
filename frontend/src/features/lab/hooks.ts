import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { AgentService, UsersService } from "@/client"

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
