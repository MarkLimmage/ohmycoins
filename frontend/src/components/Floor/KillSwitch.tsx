import { Box, Text } from "@chakra-ui/react"
import { useCallback, useEffect, useId } from "react"
import { MdCancel } from "react-icons/md"
import { SafetyButton } from "./SafetyButton"

interface KillSwitchProps {
  onKill: () => Promise<void>
  isDisabled?: boolean
}

export const KillSwitch = ({ onKill, isDisabled = false }: KillSwitchProps) => {
  const descriptionId = useId()
  const buttonId = useId()

  const handleKeyPress = useCallback(
    (event: KeyboardEvent) => {
      if (event.ctrlKey && event.shiftKey && event.key === "K") {
        event.preventDefault()
        const button = document.getElementById(buttonId)
        button?.focus()
      }
    },
    [buttonId],
  )

  useEffect(() => {
    document.addEventListener("keydown", handleKeyPress)
    return () => {
      document.removeEventListener("keydown", handleKeyPress)
    }
  }, [handleKeyPress])

  return (
    <Box
      position="fixed"
      bottom="20px"
      right="20px"
      zIndex={9999}
      role="region"
      aria-label="Emergency controls"
    >
      <Box
        id={buttonId}
        as="button"
        onClick={(e: React.MouseEvent) => {
          if (isDisabled) {
            e.preventDefault()
            return
          }
          const safetyButton = document.querySelector(
            '[aria-label="EMERGENCY STOP button"]',
          ) as HTMLButtonElement
          safetyButton?.click()
        }}
        aria-disabled={isDisabled}
        w="120px"
        h="120px"
        bg={isDisabled ? "#9ca3af" : "#dc2626"}
        color="white"
        borderRadius="md"
        display="flex"
        flexDirection="column"
        alignItems="center"
        justifyContent="center"
        cursor={isDisabled ? "not-allowed" : "pointer"}
        transition="all 0.2s"
        border="none"
        boxShadow="lg"
        pointerEvents={isDisabled ? "none" : "auto"}
        _hover={{
          bg: isDisabled ? "#9ca3af" : "#991b1b",
          transform: isDisabled ? "none" : "scale(1.05)",
        }}
        _focus={{
          outline: "2px solid",
          outlineColor: "blue.500",
          outlineOffset: "2px",
        }}
        _active={{
          transform: isDisabled ? "none" : "scale(0.95)",
        }}
        aria-label="EMERGENCY STOP button"
        aria-describedby={descriptionId}
        aria-keyshortcuts="Control+Shift+K"
      >
        <MdCancel size={48} />
        <Text
          fontSize="xs"
          fontWeight="bold"
          mt={2}
          textAlign="center"
          lineHeight="1.2"
        >
          EMERGENCY
          <br />
          STOP
        </Text>
      </Box>

      <Box id={descriptionId} position="absolute" left="-9999px">
        Press to stop all active trading algorithms and close all open
        positions. This action requires confirmation. Keyboard shortcut:
        Ctrl+Shift+K
      </Box>

      <Box position="absolute" left="-9999px" top="-9999px">
        <SafetyButton
          action="kill"
          onConfirm={onKill}
          requireConfirmation={true}
          isDisabled={isDisabled}
          cooldownSeconds={5}
          label="EMERGENCY STOP"
          description="Press to stop all active trading algorithms and close all open positions. This action requires confirmation."
        />
      </Box>

      <Box
        role="status"
        aria-live="assertive"
        aria-atomic="true"
        position="absolute"
        left="-9999px"
      />
    </Box>
  )
}
