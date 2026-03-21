import { Box, VStack } from "@chakra-ui/react"
import type React from "react"
import { LabHeader } from "./components/LabHeader"
import { StageRowList } from "./components/StageRowList"

// import { Artifact } from './components/ArtifactViewer'; // Keep if types needed for props, but we are removing props.

// type LabSessionViewProps = {}

export const LabSessionView: React.FC = () => {
  return (
    <VStack align="stretch" gap={4} h="full">
      <LabHeader />

      <Box flex={1} overflowY="auto" px={4} pb={4}>
        <StageRowList />
      </Box>
    </VStack>
  )
}
