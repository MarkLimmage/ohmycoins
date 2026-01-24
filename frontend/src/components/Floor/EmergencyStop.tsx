import { Box, Button, Input, Spinner, Text } from "@chakra-ui/react"
import { useCallback, useEffect, useId, useState } from "react"
import { MdCancel } from "react-icons/md"
import {
  DialogBody,
  DialogCloseTrigger,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogRoot,
  DialogTitle,
} from "@/components/ui/dialog"
import type { AuditLogEntry } from "./types"

interface EmergencyStopProps {
  onStop: () => Promise<void>
  isDisabled?: boolean
  consequences?: string[]
}

const auditLog = (entry: AuditLogEntry): void => {
  console.log(
    `[AUDIT] ${entry.timestamp} - ${entry.component} - ${entry.action} - User: ${entry.user}`,
  )
}

export const EmergencyStop = ({
  onStop,
  isDisabled = false,
  consequences = [
    "Cancel all pending orders",
    "Liquidate all open positions",
    "Disable all trading algorithms",
    "Block new trade execution",
  ],
}: EmergencyStopProps) => {
  const descriptionId = useId()

  const [isOpen, setIsOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [typedText, setTypedText] = useState("")
  const [cooldownRemaining, setCooldownRemaining] = useState(0)
  const [showSuccess, setShowSuccess] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const isOnCooldown = cooldownRemaining > 0
  const isConfirmDisabled = typedText !== "STOP"

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
      await onStop()
      setShowSuccess(true)
      setCooldownRemaining(5)

      auditLog({
        timestamp: new Date().toISOString(),
        action: "stop",
        user: "current-user",
        component: "EmergencyStop-Confirmed",
      })

      setTimeout(() => {
        setShowSuccess(false)
        setIsOpen(false)
        setTypedText("")
      }, 2000)
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred")
      auditLog({
        timestamp: new Date().toISOString(),
        action: "stop",
        user: "current-user",
        component: "EmergencyStop-Error",
      })
    } finally {
      setIsLoading(false)
    }
  }, [onStop])

  const handleClick = useCallback(() => {
    if (isDisabled || isOnCooldown) return

    auditLog({
      timestamp: new Date().toISOString(),
      action: "stop",
      user: "current-user",
      component: "EmergencyStop",
    })

    setIsOpen(true)
  }, [isDisabled, isOnCooldown])

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
        size="lg"
        colorScheme="red"
        aria-label="Emergency stop button"
        aria-describedby={descriptionId}
        _focus={{
          outline: "2px solid",
          outlineColor: "blue.500",
          outlineOffset: "2px",
        }}
      >
        <MdCancel size={24} />
        {isOnCooldown ? `Wait ${cooldownRemaining}s` : "EMERGENCY STOP"}
      </Button>

      <Box id={descriptionId} position="absolute" left="-9999px">
        Emergency stop all trading operations. This action requires typing STOP
        to confirm.
      </Box>

      <DialogRoot
        open={isOpen}
        onOpenChange={(e) => !isLoading && setIsOpen(e.open)}
        trapFocus
      >
        <DialogContent maxW="500px" backdrop>
          <DialogHeader>
            <DialogTitle>
              <Text color="red.600" fontSize="xl" fontWeight="bold">
                ⚠️ EMERGENCY STOP
              </Text>
            </DialogTitle>
          </DialogHeader>
          <DialogCloseTrigger onClick={handleCancel} disabled={isLoading} />
          <DialogBody>
            {showSuccess ? (
              <Box
                role="alert"
                aria-live="assertive"
                color="green.600"
                fontWeight="bold"
                fontSize="lg"
                textAlign="center"
                py={4}
              >
                ✓ Emergency stop executed successfully!
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
                    fontWeight="bold"
                  >
                    ✗ {error}
                  </Box>
                )}

                <Box
                  mb={4}
                  p={4}
                  bg="red.50"
                  borderRadius="md"
                  borderLeft="4px solid"
                  borderColor="red.600"
                >
                  <Text fontWeight="bold" color="red.700" mb={2}>
                    This will immediately:
                  </Text>
                  <Box as="ul" pl={5} color="red.700">
                    {consequences.map((consequence, index) => (
                      <Text as="li" key={index} mb={1}>
                        {consequence}
                      </Text>
                    ))}
                  </Box>
                </Box>

                <Box mb={4}>
                  <Text mb={2} fontWeight="bold" color="red.600" fontSize="md">
                    Type "STOP" to confirm this action:
                  </Text>
                  <Input
                    value={typedText}
                    onChange={(e) => setTypedText(e.target.value.toUpperCase())}
                    placeholder="STOP"
                    disabled={isLoading}
                    autoFocus
                    size="lg"
                    fontWeight="bold"
                    textAlign="center"
                    aria-label="Type STOP to confirm emergency stop"
                    _focus={{
                      outline: "2px solid",
                      outlineColor: "blue.500",
                      outlineOffset: "2px",
                    }}
                  />
                </Box>
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
                  size="lg"
                >
                  Cancel
                </Button>
                <Button
                  colorScheme="red"
                  onClick={handleConfirm}
                  disabled={isConfirmDisabled || isLoading}
                  size="lg"
                  fontWeight="bold"
                  _focus={{
                    outline: "2px solid",
                    outlineColor: "blue.500",
                    outlineOffset: "2px",
                  }}
                >
                  {isLoading ? <Spinner size="sm" /> : "CONFIRM STOP"}
                </Button>
              </>
            )}
          </DialogFooter>
        </DialogContent>
      </DialogRoot>

      <Box
        role="status"
        aria-live="assertive"
        aria-atomic="true"
        position="absolute"
        left="-9999px"
      />
    </>
  )
}
