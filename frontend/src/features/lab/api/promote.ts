import { OpenAPI } from "@/client"

interface PromoteRunPayload {
  mlflow_run_id: string
  algorithm_name: string
  signal_type: string
}

interface PromoteRunResponse {
  status: string
  message: string
  data: {
    algorithm_id: string
    name: string
    state: string
  }
}

export const promoteRunToFloor = async (
  payload: PromoteRunPayload,
): Promise<PromoteRunResponse> => {
  const baseUrl = OpenAPI.BASE
  const rawToken = OpenAPI.TOKEN
  let token: string | undefined

  if (typeof rawToken === "function") {
    token = await (rawToken as () => Promise<string>)()
  } else {
    token = rawToken
  }

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  }

  if (token) {
    headers.Authorization = `Bearer ${token}`
  }

  const response = await fetch(`${baseUrl}/api/v1/algorithms/promote`, {
    method: "POST",
    headers,
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new Error(
      errorData.detail || `Failed to promote run: ${response.statusText}`,
    )
  }

  return response.json()
}
