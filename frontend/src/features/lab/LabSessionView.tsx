import { Box, Button, VStack } from "@chakra-ui/react"
import type React from "react"
import { LabGrid } from "./components/LabGrid"
import { LabHeader } from "./components/LabHeader"
import { useLabContext } from "./context/LabContext"

// import { Artifact } from './components/ArtifactViewer'; // Keep if types needed for props, but we are removing props.

// type LabSessionViewProps = {}

export const LabSessionView: React.FC = () => {
  const { sendMessage } = useLabContext()

  return (
    <VStack align="stretch" gap={4} h="full">
      <LabHeader />

      <Box px={4}>
        <Button
          size="sm"
          colorScheme="blue"
          onClick={() => sendMessage({ type: "resume" })}
        >
          Resume Workflow (HITL)
        </Button>
      </Box>

      <Box flex={1} overflowY="auto" px={4} pb={4}>
        <LabGrid />
      </Box>
    </VStack>
  )
}
