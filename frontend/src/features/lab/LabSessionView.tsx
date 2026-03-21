import { Box, VStack } from "@chakra-ui/react"
import type React from "react"
import { LabGrid } from "./components/LabGrid"

export const LabSessionView: React.FC = () => {
  return (
    <VStack align="stretch" gap={2} h="full">
      <Box flex={1} overflowY="auto" px={2} pb={2}>
        <LabGrid />
      </Box>
    </VStack>
  )
}
