import { Box, Center, Spinner, Text } from "@chakra-ui/react"
import { useEffect, useMemo, useRef, useState } from "react"
import { getStageStatus, useLabContext } from "../context/LabContext"
import type { LabStage } from "../types"
import { StageRow } from "./StageRow"

const ORDERED_STAGES: LabStage[] = [
  "BUSINESS_UNDERSTANDING",
  "DATA_ACQUISITION",
  "PREPARATION",
  "EXPLORATION",
  "MODELING",
  "EVALUATION",
  "DEPLOYMENT",
]

export const StageRowList = () => {
  const { state, isLoading } = useLabContext()
  const [expandedStages, setExpandedStages] = useState<Set<LabStage>>(new Set())
  const rowRefs = useRef<Record<string, HTMLDivElement | null>>({})
  const prevActiveRef = useRef<LabStage | null>(null)

  // Compute current active stage (latest non-completed active)
  const currentActiveStage = useMemo(() => {
    for (let i = ORDERED_STAGES.length - 1; i >= 0; i--) {
      const s = ORDERED_STAGES[i]
      if (state.activeStages.has(s) && !state.completedStages.has(s)) {
        return s
      }
    }
    return null
  }, [state.activeStages, state.completedStages])

  // Auto-expand active stage and collapse previous when active stage changes
  useEffect(() => {
    if (currentActiveStage && currentActiveStage !== prevActiveRef.current) {
      setExpandedStages((prev) => {
        const next = new Set(prev)
        // Collapse previous active (unless user manually expanded it as complete)
        if (prevActiveRef.current) {
          next.delete(prevActiveRef.current)
        }
        next.add(currentActiveStage)
        return next
      })

      // Scroll into view
      const el = rowRefs.current[currentActiveStage]
      if (el) {
        el.scrollIntoView({ behavior: "smooth", block: "start" })
      }

      prevActiveRef.current = currentActiveStage
    }
  }, [currentActiveStage])

  const handleToggle = (stage: LabStage) => {
    const status = getStageStatus(stage, state)
    if (status === "pending") return

    setExpandedStages((prev) => {
      const next = new Set(prev)
      if (next.has(stage)) {
        next.delete(stage)
      } else {
        next.add(stage)
      }
      return next
    })
  }

  const hasContent =
    state.activeStages.size > 0 || state.dialogueMessages.length > 0

  if (!hasContent && isLoading) {
    return (
      <Center p={10} h="100%">
        <Spinner mr={3} />
        <Text>Rehydrating Session...</Text>
      </Center>
    )
  }

  return (
    <Box>
      {ORDERED_STAGES.map((stage) => {
        const status = getStageStatus(stage, state)
        const taskCount = state.activityItems.filter(
          (item) => item.stage === stage,
        ).length
        const outputCount = (state.stageOutputs[stage] || []).length

        return (
          <Box
            key={stage}
            ref={(el: HTMLDivElement | null) => {
              rowRefs.current[stage] = el
            }}
          >
            <StageRow
              stage={stage}
              status={status}
              isExpanded={expandedStages.has(stage)}
              onToggle={() => handleToggle(stage)}
              taskCount={taskCount}
              outputCount={outputCount}
            />
          </Box>
        )
      })}
    </Box>
  )
}
