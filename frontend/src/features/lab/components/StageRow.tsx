import { Box, Grid, GridItem } from "@chakra-ui/react"
import type { LabStage, StageStatus } from "../types"
import { ActivityTracker } from "./ActivityTracker"
import { DialoguePanel } from "./DialoguePanel"
import { StageOutputs } from "./StageOutputs"
import { StageRowHeader } from "./StageRowHeader"

const STATUS_COLORS: Record<StageStatus, string> = {
  active: "blue.500",
  complete: "green.500",
  pending: "gray.300",
  stale: "orange.400",
}

interface StageRowProps {
  stage: LabStage
  status: StageStatus
  isExpanded: boolean
  onToggle: () => void
  taskCount?: number
  outputCount?: number
}

export const StageRow = ({
  stage,
  status,
  isExpanded,
  onToggle,
  taskCount,
  outputCount,
}: StageRowProps) => {
  return (
    <Box
      borderLeft="4px solid"
      borderLeftColor={STATUS_COLORS[status]}
      borderRadius="md"
      mb={3}
      bg="white"
      shadow="sm"
      border="1px solid"
      borderColor="gray.200"
    >
      <StageRowHeader
        stage={stage}
        status={status}
        onToggle={onToggle}
        isExpanded={isExpanded}
        taskCount={taskCount}
        outputCount={outputCount}
      />
      {isExpanded && (
        <Grid
          templateColumns="2fr 1fr 1fr"
          gap={2}
          maxH="450px"
          p={3}
          borderTop="1px solid"
          borderColor="gray.100"
        >
          <GridItem overflowY="auto" h="100%">
            <DialoguePanel stage={stage} />
          </GridItem>
          <GridItem overflowY="auto" h="100%">
            <ActivityTracker stage={stage} />
          </GridItem>
          <GridItem overflowY="auto" h="100%">
            <StageOutputs stage={stage} />
          </GridItem>
        </Grid>
      )}
    </Box>
  )
}
