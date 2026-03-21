// Workstream E: Lab Types
// Spec: WORKER_MISSION.md v1.3

export type LabStage =
  | "BUSINESS_UNDERSTANDING"
  | "DATA_ACQUISITION"
  | "PREPARATION"
  | "EXPLORATION"
  | "MODELING"
  | "EVALUATION"
  | "DEPLOYMENT"

export type LabMimeType =
  | "text/markdown"
  | "application/vnd.plotly.v1+json"
  | "application/json+blueprint"
  | "application/json+tearsheet"
  | "image/png"

export interface LabEventPayload {
  [key: string]: any
}

export type LabEventType =
  | "stream_chat"
  | "status_update"
  | "render_output"
  | "error"
  | "action_request"
  | "user_message"
  | "plan_established"
  | "revision_start"

export type StageStatus = "pending" | "active" | "complete" | "stale"

export interface LabEvent {
  event_type: LabEventType
  stage: LabStage
  sequence_id: number
  timestamp: string // ISO-8601
  payload: LabEventPayload
}

export interface LabCell {
  id: string // sequence_id as string
  stage: LabStage
  type: LabMimeType
  content: any
  timestamp: string
  metadata?: any
}

export interface ActionRequest {
  action_id: string
  description: string
  options: string[]
  title?: string // Optional title for the action
}

// G7: Updated State Shape
export interface DialogueMessage {
  id: string
  type: "agent" | "user" | "error" | "action_request" | "divider"
  content: string
  timestamp: string
  sequence_id: number
  stage?: LabStage
  actionPayload?: LabEventPayload // Full payload for action_request events
  resolved?: boolean // Whether the HITL action has been resolved
  resolvedOption?: string // Which option the user chose
}

export interface ActivityItem {
  id: string // task_id
  description: string
  status: "pending" | "active" | "completed" | "failed"
  stage: LabStage
  sequence_id: number
}

export interface MasterPlan {
  stages: Record<LabStage, ActivityItem[]>
}

export interface LabState {
  sessionId: string | null

  // G6: 3-Cell Data Structures

  // Left Cell: Dialogue
  dialogueMessages: DialogueMessage[]
  pendingAction: ActionRequest | null

  // Center Cell: Activity
  masterPlan: MasterPlan | null
  activityItems: ActivityItem[] // Flattened or processed list of current activities

  // Right Cell: Outputs (Stage-Isolated)
  stageOutputs: Record<LabStage, LabCell[]>

  // Selection State
  selectedStage: LabStage | null
  activeStages: Set<LabStage>
  completedStages: Set<LabStage>
  staleStages: Set<LabStage>

  lastSequenceId: number
  isConnected: boolean
  isDone: boolean
  metrics: any[]
  blueprint: any | null
  // Legacy support
  stages?: Record<LabStage, LabCell[]>
}
