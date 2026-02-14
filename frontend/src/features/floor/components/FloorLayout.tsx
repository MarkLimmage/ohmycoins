import { Box, VStack } from "@chakra-ui/react"
import { useFloorWebSocket } from "../hooks/useFloorWebSocket"
import { useTradingControls } from "../hooks/useTradingControls"
import { AlgorithmGrid } from "./AlgorithmGrid"
import { KillSwitch } from "./KillSwitch"
import { PLTicker } from "./PLTicker"

export const FloorLayout = () => {
  const { tickerData, algorithms } = useFloorWebSocket()
  const { pauseAlgorithm, resumeAlgorithm, stopAlgorithm, emergencyStop } =
    useTradingControls()

  return (
    <Box minH="100vh" bg="gray.50" position="relative">
      <Box position="sticky" top={0} zIndex={50}>
        <PLTicker data={tickerData} />
      </Box>

      <Box p={6} pb={32}>
        {" "}
        {/* Padding bottom for KillSwitch space */}
        <VStack align="stretch">
          <AlgorithmGrid
            algorithms={algorithms}
            onPause={pauseAlgorithm}
            onResume={resumeAlgorithm}
            onStop={stopAlgorithm}
          />
        </VStack>
      </Box>

      <KillSwitch
        onEmergencyStop={emergencyStop}
        isActive={algorithms.some((a) => a.status === "active")}
      />
    </Box>
  )
}
