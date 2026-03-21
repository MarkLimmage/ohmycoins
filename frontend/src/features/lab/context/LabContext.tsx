// Workstream G: Lab Context Refactor (Scientific Grid)
import type React from "react"
import {
  createContext,
  type ReactNode,
  useCallback,
  useContext,
  useEffect,
  useReducer,
  useState,
} from "react"
import { useLabWebSocket } from "../hooks/useLabWebSocket"
import { useRehydration } from "../hooks/useRehydration"
import type {
  ActivityItem,
  DialogueMessage,
  LabCell,
  LabEvent,
  LabStage,
  LabState,
  StageStatus,
} from "../types"

type Action =
  | { type: "SET_SESSION"; payload: string | null }
  | {
      type: "REHYDRATE"
      payload: { ledger: LabEvent[]; lastSequenceId: number }
    }
  | { type: "PROCESS_EVENT"; payload: LabEvent }
  | { type: "SET_CONNECTION_STATUS"; payload: { isConnected: boolean } }
  | { type: "SET_DONE"; payload: boolean }
  | { type: "CLEAR_ACTION" }
  | { type: "SET_SELECTED_STAGE"; payload: LabStage | null }
  | { type: "RESOLVE_ACTION"; payload: { messageId: string; option: string } }
  | { type: "MARK_STAGE_COMPLETE"; payload: LabStage }
  | { type: "MARK_STAGES_STALE"; payload: LabStage[] }
  | { type: "CLEAR_STALE"; payload: LabStage[] }

const initialState: LabState = {
  sessionId: null,
  dialogueMessages: [],
  pendingAction: null,
  masterPlan: null,
  activityItems: [],
  stageOutputs: {
    BUSINESS_UNDERSTANDING: [],
    DATA_ACQUISITION: [],
    PREPARATION: [],
    EXPLORATION: [],
    MODELING: [],
    EVALUATION: [],
    DEPLOYMENT: [],
  },
  selectedStage: null,
  activeStages: new Set(),
  completedStages: new Set(),
  staleStages: new Set(),
  lastSequenceId: 0,
  isConnected: false,
  isDone: false,
  metrics: [],
  blueprint: null,
  stages: {} as any, // Legacy
}

function labReducer(state: LabState, action: Action): LabState {
  switch (action.type) {
    case "SET_SESSION":
      return {
        ...initialState,
        sessionId: action.payload,
      }

    case "SET_CONNECTION_STATUS":
      return { ...state, isConnected: action.payload.isConnected }

    case "SET_DONE":
      return { ...state, isDone: action.payload }

    case "CLEAR_ACTION":
      return { ...state, pendingAction: null }

    case "SET_SELECTED_STAGE":
      return { ...state, selectedStage: action.payload }

    case "RESOLVE_ACTION": {
      const updatedMessages = state.dialogueMessages.map((msg) =>
        msg.id === action.payload.messageId
          ? { ...msg, resolved: true, resolvedOption: action.payload.option }
          : msg,
      )
      return {
        ...state,
        dialogueMessages: updatedMessages,
        pendingAction: null,
      }
    }

    case "MARK_STAGE_COMPLETE": {
      const newCompleted = new Set(state.completedStages)
      newCompleted.add(action.payload)
      return { ...state, completedStages: newCompleted }
    }

    case "MARK_STAGES_STALE": {
      const newStale = new Set(state.staleStages)
      for (const s of action.payload) newStale.add(s)
      return { ...state, staleStages: newStale }
    }

    case "CLEAR_STALE": {
      const newStale = new Set(state.staleStages)
      for (const s of action.payload) newStale.delete(s)
      return { ...state, staleStages: newStale }
    }

    case "REHYDRATE": {
      // Sort ledger by sequence_id
      const sortedLedger = [...action.payload.ledger].sort(
        (a, b) => a.sequence_id - b.sequence_id,
      )

      // Replay events to build state
      let newState = { ...state, lastSequenceId: action.payload.lastSequenceId }

      // Reset detailed state before replaying
      newState = {
        ...newState,
        dialogueMessages: [],
        activityItems: [],
        stageOutputs: {
          BUSINESS_UNDERSTANDING: [],
          DATA_ACQUISITION: [],
          PREPARATION: [],
          EXPLORATION: [],
          MODELING: [],
          EVALUATION: [],
          DEPLOYMENT: [],
        },
        activeStages: new Set(),
        completedStages: new Set(),
        staleStages: new Set(),
        pendingAction: null,
      }

      for (const event of sortedLedger) {
        newState = processEvent(newState, event)
      }
      return newState
    }

    case "PROCESS_EVENT": {
      const event = action.payload

      // Discard out-of-order events
      if (event.sequence_id <= state.lastSequenceId) {
        return state
      }

      return processEvent(state, event)
    }

    default:
      return state
  }
}

const ORDERED_STAGES: LabStage[] = [
  "BUSINESS_UNDERSTANDING",
  "DATA_ACQUISITION",
  "PREPARATION",
  "EXPLORATION",
  "MODELING",
  "EVALUATION",
  "DEPLOYMENT",
]

/** Return the latest (highest-index) active stage, or fallback */
function getLatestActiveStage(state: LabState): LabStage {
  for (let i = ORDERED_STAGES.length - 1; i >= 0; i--) {
    if (
      state.activeStages.has(ORDERED_STAGES[i]) &&
      !state.completedStages.has(ORDERED_STAGES[i])
    ) {
      return ORDERED_STAGES[i]
    }
  }
  // Fallback to any active stage or first stage
  for (let i = ORDERED_STAGES.length - 1; i >= 0; i--) {
    if (state.activeStages.has(ORDERED_STAGES[i])) {
      return ORDERED_STAGES[i]
    }
  }
  return "BUSINESS_UNDERSTANDING"
}

/** Compute the display status for a given stage */
export function getStageStatus(stage: LabStage, state: LabState): StageStatus {
  if (state.staleStages.has(stage)) return "stale"
  if (state.activeStages.has(stage) && !state.completedStages.has(stage))
    return "active"
  if (state.completedStages.has(stage)) return "complete"
  return "pending"
}

function processEvent(state: LabState, event: LabEvent): LabState {
  const { event_type, stage, payload, sequence_id, timestamp } = event

  let newState = {
    ...state,
    lastSequenceId: Math.max(state.lastSequenceId, sequence_id),
  }

  // Update active stages + stage lifecycle
  if (stage) {
    if (
      event_type === "status_update" &&
      String(payload.status).toUpperCase() === "ACTIVE"
    ) {
      if (!newState.activeStages.has(stage)) {
        const newActive = new Set(newState.activeStages)
        newActive.add(stage)
        newState.activeStages = newActive
      }
      // Remove from completed/stale if re-activated
      if (newState.completedStages.has(stage)) {
        const newCompleted = new Set(newState.completedStages)
        newCompleted.delete(stage)
        newState.completedStages = newCompleted
      }
      if (newState.staleStages.has(stage)) {
        const newStale = new Set(newState.staleStages)
        newStale.delete(stage)
        newState.staleStages = newStale
      }
    }

    if (
      event_type === "status_update" &&
      String(payload.status).toUpperCase() === "COMPLETE"
    ) {
      const newCompleted = new Set(newState.completedStages)
      newCompleted.add(stage)
      newState.completedStages = newCompleted
    }

    if (
      event_type === "status_update" &&
      String(payload.status).toUpperCase() === "STALE"
    ) {
      const newStale = new Set(newState.staleStages)
      newStale.add(stage)
      newState.staleStages = newStale
    }

    if (event_type === "render_output") {
      if (!newState.activeStages.has(stage)) {
        const newActive = new Set(newState.activeStages)
        newActive.add(stage)
        newState.activeStages = newActive
      }
    }
  }

  // Handle revision_start
  if (event_type === "revision_start") {
    // Add divider message to dialogue
    const divider: DialogueMessage = {
      id: String(sequence_id),
      type: "divider",
      content: `--- Revision: ${stage} ---`,
      timestamp,
      sequence_id,
      stage,
    }
    newState.dialogueMessages = [...newState.dialogueMessages, divider]

    // Mark downstream stages as stale
    const staleList: LabStage[] = payload.stale_stages || []
    if (staleList.length > 0) {
      const newStale = new Set(newState.staleStages)
      for (const s of staleList) newStale.add(s as LabStage)
      newState.staleStages = newStale
    }

    // Re-activate the revised stage
    if (stage) {
      const newActive = new Set(newState.activeStages)
      newActive.add(stage)
      newState.activeStages = newActive
      const newCompleted = new Set(newState.completedStages)
      newCompleted.delete(stage)
      newState.completedStages = newCompleted
    }

    return newState
  }

  // --- ROUTING ---

  // 1. LEFT CELL (Dialogue)
  if (
    event_type === "stream_chat" ||
    event_type === "user_message" ||
    event_type === "error" ||
    event_type === "action_request"
  ) {
    const content =
      payload.text_delta ||
      payload.content ||
      payload.message ||
      payload.description ||
      ""

    const msgType =
      event_type === "user_message"
        ? ("user" as const)
        : event_type === "error"
          ? ("error" as const)
          : event_type === "action_request"
            ? ("action_request" as const)
            : ("agent" as const)

    const message: DialogueMessage = {
      id: String(sequence_id),
      type: msgType,
      content: content,
      timestamp,
      sequence_id,
      stage: stage || getLatestActiveStage(newState),
      ...(event_type === "action_request" ? { actionPayload: payload } : {}),
    }

    // Only add to dialogue if it has content to show
    if (message.content || event_type === "action_request") {
      newState.dialogueMessages = [...newState.dialogueMessages, message]
    }

    if (event_type === "action_request") {
      newState.pendingAction = {
        action_id: payload.action_id,
        description: payload.description,
        options: payload.options,
        title: payload.title,
      }
    }
  }

  // 2. CENTER CELL (Activity Tracker)
  if (event_type === "plan_established") {
    if (payload.stages) {
      const newItems: ActivityItem[] = []
      Object.entries(payload.stages).forEach(
        ([stageKey, items]: [string, any]) => {
          if (Array.isArray(items)) {
            items.forEach((item) => {
              newItems.push({
                id: item.id,
                description: item.description,
                status: item.status || "pending",
                stage: stageKey as LabStage,
                sequence_id,
              })
            })
          }
        },
      )
      newState.activityItems = newItems
      newState.masterPlan = payload.stages
    }
  }

  if (event_type === "status_update") {
    const { task_id, status, message } = payload

    if (task_id) {
      const index = newState.activityItems.findIndex(
        (item) => item.id === task_id,
      )
      if (index !== -1) {
        const updatedItems = [...newState.activityItems]
        updatedItems[index] = {
          ...updatedItems[index],
          status: status || updatedItems[index].status,
        }
        newState.activityItems = updatedItems
      } else {
        // Fallback
        newState.activityItems = [
          ...newState.activityItems,
          {
            id: task_id,
            description: message || `Task ${task_id}`,
            status: status || "pending",
            stage: stage || "BUSINESS_UNDERSTANDING",
            sequence_id,
          },
        ]
      }
    }
  }

  // 3. RIGHT CELL (Stage Outputs)
  if (event_type === "render_output") {
    const targetStage = stage || "BUSINESS_UNDERSTANDING"
    const currentStageOutputs = newState.stageOutputs[targetStage] || []

    if (!currentStageOutputs.some((c) => c.id === String(sequence_id))) {
      const newCell: LabCell = {
        id: String(sequence_id),
        stage: targetStage,
        type: payload.mime_type || "text/markdown",
        content: payload.content || "",
        timestamp,
        metadata: payload.metadata,
      }

      newState = {
        ...newState,
        stageOutputs: {
          ...newState.stageOutputs,
          [targetStage]: [...currentStageOutputs, newCell],
        },
      }

      if (newCell.type === "application/json+blueprint") {
        let blueprintData = newCell.content
        if (typeof blueprintData === "string") {
          try {
            blueprintData = JSON.parse(blueprintData)
          } catch {}
        }
        newState.blueprint = blueprintData
      }
    }
  }

  return newState
}

const LabContext = createContext<
  | {
      state: LabState
      dispatch: React.Dispatch<Action>
      sendMessage: (message: any) => void
      isLoading: boolean
    }
  | undefined
>(undefined)

export function LabProvider({
  children,
  sessionId,
}: {
  children: ReactNode
  sessionId: string | null
}) {
  const [state, dispatch] = useReducer(labReducer, initialState)
  const { rehydrate, isRehydrating } = useRehydration()
  const [rehydrated, setRehydrated] = useState(false)
  const [afterSeq, setAfterSeq] = useState<number | undefined>(undefined)

  // Handle WebSocket events
  const onEvent = useCallback((event: LabEvent) => {
    dispatch({ type: "PROCESS_EVENT", payload: event })
  }, [])

  // Connect WS only after rehydration completes (with after_seq to prevent duplicates)
  const { isConnected, sendMessage } = useLabWebSocket({
    sessionId,
    enabled: !!sessionId && rehydrated,
    afterSeq,
    onEvent,
  })

  // Sync connection status
  useEffect(() => {
    dispatch({ type: "SET_CONNECTION_STATUS", payload: { isConnected } })
  }, [isConnected])

  // Handle Session Change: rehydrate first, then enable WS
  useEffect(() => {
    dispatch({ type: "SET_SESSION", payload: sessionId })
    setRehydrated(false)
    setAfterSeq(undefined)

    if (sessionId) {
      rehydrate(sessionId).then((data) => {
        if (data) {
          dispatch({
            type: "REHYDRATE",
            payload: {
              ledger: data.event_ledger,
              lastSequenceId: data.last_sequence_id,
            },
          })
          setAfterSeq(data.last_sequence_id)
        }
        setRehydrated(true)
      })
    }
  }, [sessionId, rehydrate])

  return (
    <LabContext.Provider
      value={{ state, dispatch, sendMessage, isLoading: isRehydrating }}
    >
      {children}
    </LabContext.Provider>
  )
}

export const useLabContext = () => {
  const context = useContext(LabContext)
  if (context === undefined) {
    throw new Error("useLabContext must be used within a LabProvider")
  }
  return context
}
