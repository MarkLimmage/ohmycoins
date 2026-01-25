import { Box, Button, Flex, Text, Badge } from "@chakra-ui/react"
import { SafetyButton } from "@/components/Floor"
import type { AlgorithmData } from "../types"

interface AlgorithmCardProps {
  algorithm: AlgorithmData
  onPause: (id: string) => void
  onResume: (id: string) => void
  onStop: (id: string) => Promise<void>
}

export const AlgorithmCard = ({
  algorithm,
  onPause,
  onResume,
  onStop,
}: AlgorithmCardProps) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case "active":
        return "#10b981"
      case "paused":
        return "#f59e0b"
      case "stopped":
      case "error":
        return "#ef4444"
      case "initializing":
        return "#3b82f6"
      default:
        return "#d1d5db"
    }
  }

  const borderColor = getStatusColor(algorithm.status)

  const formatUptime = (seconds: number) => {
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = seconds % 60
    return `${minutes}m ${remainingSeconds}s`
  }

  return (
    <Box
      borderWidth="2px"
      borderStyle="solid"
      borderColor={borderColor}
      borderRadius="lg"
      p={4}
      w="full"
      boxShadow="md"
      _hover={{ boxShadow: "lg" }}
      bg="white"
      color="black"
    >
      <Text fontWeight="bold" fontSize="16px" mb={2}>
        {algorithm.name}
      </Text>

      <Flex justifyContent="space-between" mb={2} alignItems="center">
        <Box>
            <Text fontSize="20px" fontWeight="bold">
            {algorithm.pnl_amount >= 0 ? "+" : ""}${algorithm.pnl_amount.toFixed(2)}{" "}
            <Text as="span" fontSize="sm" color={algorithm.pnl_percentage >= 0 ? "green.600" : "red.600"}>
                ({(algorithm.pnl_percentage * 100).toFixed(1)}%)
            </Text>
            </Text>
        </Box>
        <Badge colorPalette={algorithm.status === 'active' ? 'green' : algorithm.status === 'paused' ? 'orange' : 'red'}>
            {algorithm.status.toUpperCase()}
        </Badge>
      </Flex>

      <Text fontSize="sm" color="gray.600">Uptime: {formatUptime(algorithm.uptime_seconds)}</Text>
      <Text fontSize="sm" color="gray.600">
        Trades: {algorithm.trade_count} ({algorithm.win_count} wins, {algorithm.loss_count} losses)
      </Text>
      <Text fontSize="sm" color="gray.600" mb={4}>
        Win Rate: {algorithm.trade_count > 0 ? ((algorithm.win_count / algorithm.trade_count) * 100).toFixed(1) : 0}%
      </Text>

      <Flex gap={2} mt={4}>
        {algorithm.status === "active" && (
          <Button size="sm" onClick={() => onPause(algorithm.id)} colorScheme="orange">
            ⏸ Pause
          </Button>
        )}
        {algorithm.status === "paused" && (
          <Button size="sm" onClick={() => onResume(algorithm.id)} colorScheme="green">
            ▶ Resume
          </Button>
        )}
        
        <SafetyButton
            action="stop"
            onConfirm={async () => await onStop(algorithm.id)}
            requireConfirmation={true}
            confirmationText="STOP"
            label="Stop Algorithm"
            buttonSize="sm"
        >
            🛑 Stop
        </SafetyButton>
      </Flex>

      {algorithm.status === 'error' && (
          <Text color="red.500" mt={2} fontSize="sm">ERROR - {algorithm.status_message}</Text>
      )}
    </Box>
  )
}
