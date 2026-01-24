export interface SafetyButtonProps {
  action: "kill" | "confirm" | "stop"
  onConfirm: () => Promise<void>
  requireConfirmation: boolean
  confirmationText?: string
  isDisabled?: boolean
  cooldownSeconds?: number
  children?: React.ReactNode
  label?: string
  description?: string
  buttonSize?: "sm" | "md" | "lg" | "xl" | "2xl" | "2xs" | "xs"
  colorScheme?: string
}

export interface AuditLogEntry {
  timestamp: string
  action: "kill" | "confirm" | "stop"
  user: string
  component: string
}
