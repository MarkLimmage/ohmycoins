import { Box, SimpleGrid, Text } from "@chakra-ui/react"
import type { AlgorithmData } from "../types"
import { AlgorithmCard } from "./AlgorithmCard"

interface AlgorithmGridProps {
  algorithms: AlgorithmData[]
  onPause: (id: string) => Promise<void>
  onResume: (id: string) => Promise<void>
  onStop: (id: string) => Promise<void>
}

export const AlgorithmGrid = ({
  algorithms,
  onPause,
  onResume,
  onStop,
}: AlgorithmGridProps) => {
  return (
    <>
      {/* Mobile Warning - Visible only on small screens */}
      <Box
        display={{ base: "block", md: "none" }}
        p={4}
        bg="gray.100"
        borderRadius="md"
        textAlign="center"
      >
        <Text fontSize="lg" fontWeight="bold" mb={2}>
          ⚠️ Desktop Only
        </Text>
        <Text>
          Trading controls are only available on desktop devices for safety
          reasons.
        </Text>
      </Box>

      {/* Grid - Visible on medium screens and up */}
      <Box display={{ base: "none", md: "block" }} w="full">
        <SimpleGrid columns={{ base: 1, md: 2, xl: 3 }} gap={4} w="full">
          {algorithms.map((algo) => (
            <AlgorithmCard
              key={algo.id}
              algorithm={algo}
              onPause={onPause}
              onResume={onResume}
              onStop={onStop}
            />
          ))}
        </SimpleGrid>
      </Box>
    </>
  )
}
