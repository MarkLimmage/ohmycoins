import type { ButtonProps } from "@chakra-ui/react"

export interface SafetyButtonProps extends Omit<ButtonProps, "action"> {
  action: string
  onConfirm: () => Promise<void> | void
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
  action: string
  user: string
  component: string
}
