import { Box, Button, Input, Spinner, Text } from "@chakra-ui/react"
import { useCallback, useEffect, useState } from "react"
import {
  DialogBody,
  DialogCloseTrigger,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogRoot,
  DialogTitle,
} from "@/components/ui/dialog"
import type { AuditLogEntry, SafetyButtonProps } from "./types"

const auditLog = (entry: AuditLogEntry): void => {
  console.log(
    `[AUDIT] ${entry.timestamp} - ${entry.component} - ${entry.action} - User: ${entry.user}`,
  )
}

export const SafetyButton = ({
  action,
  onConfirm,
  requireConfirmation,
  confirmationText,
  isDisabled = false,
  cooldownSeconds = 5,
  children,
  label,
  description,
  buttonSize = "md",
  colorScheme = "red",
  ...props
}: SafetyButtonProps) => {
  const [isOpen, setIsOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [typedText, setTypedText] = useState("")
  const [cooldownRemaining, setCooldownRemaining] = useState(0)
  const [showSuccess, setShowSuccess] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const isOnCooldown = cooldownRemaining > 0
  const needsTypedConfirmation = confirmationText && confirmationText.length > 0
  const isConfirmDisabled =
    needsTypedConfirmation && typedText !== confirmationText

  useEffect(() => {
    if (cooldownRemaining > 0) {
      const timer = setTimeout(() => {
        setCooldownRemaining(cooldownRemaining - 1)
      }, 1000)
      return () => clearTimeout(timer)
    }
  }, [cooldownRemaining])

  const handleConfirm = useCallback(async () => {
    setIsLoading(true)
    setError(null)

    try {
      await onConfirm()
      setShowSuccess(true)
      setCooldownRemaining(cooldownSeconds)

      auditLog({
        timestamp: new Date().toISOString(),
        action,
        user: "current-user",
        component: "SafetyButton-Confirmed",
      })

      setTimeout(() => {
        setShowSuccess(false)
        setIsOpen(false)
        setTypedText("")
      }, 2000)
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred")
    } finally {
      setIsLoading(false)
    }
  }, [onConfirm, action, cooldownSeconds])

  const handleClick = useCallback(() => {
    if (isDisabled || isOnCooldown) return

    auditLog({
      timestamp: new Date().toISOString(),
      action,
      user: "current-user",
      component: "SafetyButton",
    })

    if (requireConfirmation) {
      setIsOpen(true)
    } else {
      handleConfirm()
    }
  }, [isDisabled, isOnCooldown, action, requireConfirmation, handleConfirm])

  const handleCancel = useCallback(() => {
    setIsOpen(false)
    setTypedText("")
    setError(null)
  }, [])

  return (
    <>
      <Button
        onClick={handleClick}
        disabled={isDisabled || isOnCooldown}
        size={buttonSize}
        colorScheme={colorScheme}
        {...props}
        aria-label={label || `${action} action button`}
        aria-describedby={description ? `${action}-description` : undefined}
        _focus={{
          outline: "2px solid",
          outlineColor: "blue.500",
          outlineOffset: "2px",
        }}
      >
        {isOnCooldown ? `Wait ${cooldownRemaining}s` : children || label}
      </Button>

      {description && (
        <Box id={`${action}-description`} className="visually-hidden">
          {description}
        </Box>
      )}

      <DialogRoot
        open={isOpen}
        onOpenChange={(e) => !isLoading && setIsOpen(e.open)}
        trapFocus
      >
        <DialogContent backdrop>
          <DialogHeader>
            <DialogTitle>Confirm Action</DialogTitle>
          </DialogHeader>
          <DialogCloseTrigger onClick={handleCancel} disabled={isLoading} />
          <DialogBody>
            {showSuccess ? (
              <Box
                role="alert"
                aria-live="assertive"
                color="green.600"
                fontWeight="bold"
              >
                Action completed successfully!
              </Box>
            ) : (
              <>
                {error && (
                  <Box
                    role="alert"
                    aria-live="assertive"
                    color="red.600"
                    mb={4}
                    p={3}
                    bg="red.50"
                    borderRadius="md"
                  >
                    {error}
                  </Box>
                )}

                <Text mb={4}>
                  Are you sure you want to proceed with this action?
                </Text>

                {needsTypedConfirmation && (
                  <Box mb={4}>
                    <Text mb={2} fontWeight="bold" color="red.600">
                      Type "{confirmationText}" to confirm:
                    </Text>
                    <Input
                      value={typedText}
                      onChange={(e) => setTypedText(e.target.value)}
                      placeholder={confirmationText}
                      disabled={isLoading}
                      autoFocus
                      aria-label={`Type ${confirmationText} to confirm`}
                      _focus={{
                        outline: "2px solid",
                        outlineColor: "blue.500",
                        outlineOffset: "2px",
                      }}
                    />
                  </Box>
                )}
              </>
            )}
          </DialogBody>
          <DialogFooter gap={3}>
            {!showSuccess && (
              <>
                <Button
                  variant="outline"
                  onClick={handleCancel}
                  disabled={isLoading}
                >
                  Cancel
                </Button>
                <Button
                  colorScheme="red"
                  onClick={handleConfirm}
                  disabled={isConfirmDisabled || isLoading}
                  _focus={{
                    outline: "2px solid",
                    outlineColor: "blue.500",
                    outlineOffset: "2px",
                  }}
                >
                  {isLoading ? <Spinner size="sm" /> : "Confirm"}
                </Button>
              </>
            )}
          </DialogFooter>
        </DialogContent>
      </DialogRoot>
    </>
  )
}
