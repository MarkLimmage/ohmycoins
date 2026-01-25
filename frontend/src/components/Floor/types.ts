import type { ButtonProps } from "@chakra-ui/react"

export interface SafetyButtonProps extends Omit<ButtonProps, 'action'> {
  action: "kill" | "confirm" | "stop"
  onConfirm: () => Promise<void>
  requireConfirmation: boolean
  confirmationText?: string
  isDisabled?: boolean
  cooldownSeconds?: number
  children?: React.ReactNode
  label?: string
  description?: string
  // Map buttonSize to size for backward compatibility if needed, or rely on ButtonProps size
  buttonSize?: ButtonProps["size"]
}

export interface AuditLogEntry {
  timestamp: string
  action: "kill" | "confirm" | "stop"
  user: string
  component: string
}
