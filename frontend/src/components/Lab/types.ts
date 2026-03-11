export interface AgentTerminalProps {
  sessionId: string
  streamUrl: string
  allowInteraction: boolean
  onExport?: () => void
  onCancel?: () => void
}

export interface AgentMessage {
  id: string
  type:
    | "thought"
    | "tool"
    | "result"
    | "input_request"
    | "output"
    | "blueprint"
    | "metric"
  content: string
  timestamp: string
  metadata?: {
    tool_name?: string
    execution_time?: number
    error?: string
    // Allow any other metadata for detailed step info
    [key: string]: any
  }
}

export interface MessageTypeConfig {
  color: string
  bgColor?: string
  icon?: string
  fontWeight?: string
  fontStyle?: string
}
