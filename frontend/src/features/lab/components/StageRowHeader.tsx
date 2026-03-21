import { Box, Button, Flex, Icon, Spinner, Text } from "@chakra-ui/react"
import {
  FiAlertTriangle,
  FiCheck,
  FiChevronDown,
  FiChevronRight,
  FiCircle,
} from "react-icons/fi"
import type { LabStage, StageStatus } from "../types"

const STAGE_LABELS: Record<LabStage, string> = {
  BUSINESS_UNDERSTANDING: "1. Business Understanding",
  DATA_ACQUISITION: "2. Data Acquisition",
  PREPARATION: "3. Preparation",
  EXPLORATION: "4. Exploration",
  MODELING: "5. Modeling",
  EVALUATION: "6. Evaluation",
  DEPLOYMENT: "7. Deployment",
}

const StatusIndicator = ({ status }: { status: StageStatus }) => {
  switch (status) {
    case "active":
      return <Spinner size="xs" color="blue.500" />
    case "complete":
      return <Icon as={FiCheck} color="green.500" />
    case "stale":
      return <Icon as={FiAlertTriangle} color="orange.400" />
    default:
      return <Icon as={FiCircle} color="gray.300" />
  }
}

interface StageRowHeaderProps {
  stage: LabStage
  status: StageStatus
  isExpanded: boolean
  onToggle: () => void
  taskCount?: number
  outputCount?: number
}

export const StageRowHeader = ({
  stage,
  status,
  isExpanded,
  onToggle,
  taskCount,
  outputCount,
}: StageRowHeaderProps) => {
  const isExpandable = status !== "pending"

  return (
    <Flex
      align="center"
      h="48px"
      px={3}
      cursor={isExpandable ? "pointer" : "default"}
      onClick={isExpandable ? onToggle : undefined}
      _hover={isExpandable ? { bg: "gray.50" } : undefined}
      userSelect="none"
    >
      {/* Status indicator */}
      <Box mr={3}>
        <StatusIndicator status={status} />
      </Box>

      {/* Stage name */}
      <Text
        fontSize="sm"
        fontWeight={status === "active" ? "bold" : "medium"}
        color={status === "pending" ? "gray.400" : "gray.800"}
        flex={1}
      >
        {STAGE_LABELS[stage]}
      </Text>

      {/* Collapsed summary for complete/stale */}
      {!isExpanded && (status === "complete" || status === "stale") && (
        <Text fontSize="xs" color="gray.400" mr={3}>
          {taskCount ?? 0} tasks, {outputCount ?? 0} outputs
        </Text>
      )}

      {/* Stub action buttons */}
      {status === "complete" && (
        <Button
          size="xs"
          variant="ghost"
          colorScheme="blue"
          mr={2}
          onClick={(e) => {
            e.stopPropagation()
            // Stub: Phase 7.2.3 will wire revision
          }}
        >
          Revise
        </Button>
      )}

      {status === "stale" && (
        <Flex gap={1} mr={2}>
          <Button
            size="xs"
            variant="ghost"
            colorScheme="orange"
            onClick={(e) => {
              e.stopPropagation()
              // Stub: Phase 7.2.3 will wire re-run
            }}
          >
            Re-run
          </Button>
          <Button
            size="xs"
            variant="ghost"
            onClick={(e) => {
              e.stopPropagation()
              // Stub: Phase 7.2.3 will wire keep
            }}
          >
            Keep
          </Button>
        </Flex>
      )}

      {/* Expand/collapse chevron */}
      {isExpandable && (
        <Icon
          as={isExpanded ? FiChevronDown : FiChevronRight}
          color="gray.500"
        />
      )}
    </Flex>
  )
}
