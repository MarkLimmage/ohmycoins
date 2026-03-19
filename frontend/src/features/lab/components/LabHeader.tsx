import type React from "react"
import { useMemo } from "react"
import ReactFlow, {
  Background,
  type Edge,
  type Node,
  Position,
} from "reactflow"
import "reactflow/dist/style.css"
import { Box } from "@chakra-ui/react"
import { useLabContext } from "../context/LabContext"
import type { LabStage } from "../types"

const initialNodes: Node[] = [
  {
    id: "BUSINESS_UNDERSTANDING",
    position: { x: 0, y: 50 },
    data: { label: "Business Understanding" },
    type: "input",
    sourcePosition: Position.Right,
    targetPosition: Position.Left,
  },
  {
    id: "DATA_ACQUISITION",
    position: { x: 200, y: 50 },
    data: { label: "Data Acquisition" },
    type: "default",
    sourcePosition: Position.Right,
    targetPosition: Position.Left,
  },
  {
    id: "PREPARATION",
    position: { x: 400, y: 50 },
    data: { label: "Preparation" },
    type: "default",
    sourcePosition: Position.Right,
    targetPosition: Position.Left,
  },
  {
    id: "EXPLORATION",
    position: { x: 600, y: 50 },
    data: { label: "Exploration" },
    type: "default",
    sourcePosition: Position.Right,
    targetPosition: Position.Left,
  },
  {
    id: "MODELING",
    position: { x: 800, y: 50 },
    data: { label: "Modeling" },
    type: "default",
    sourcePosition: Position.Right,
    targetPosition: Position.Left,
  },
  {
    id: "EVALUATION",
    position: { x: 1000, y: 50 },
    data: { label: "Evaluation" },
    type: "default",
    sourcePosition: Position.Right,
    targetPosition: Position.Left,
  },
  {
    id: "DEPLOYMENT",
    position: { x: 1200, y: 50 },
    data: { label: "Deployment" },
    type: "output",
    sourcePosition: Position.Right,
    targetPosition: Position.Left,
  },
]

const initialEdges: Edge[] = [
  {
    id: "e1-2",
    source: "BUSINESS_UNDERSTANDING",
    target: "DATA_ACQUISITION",
    animated: true,
  },
  {
    id: "e2-3",
    source: "DATA_ACQUISITION",
    target: "PREPARATION",
    animated: true,
  },
  { id: "e3-4", source: "PREPARATION", target: "EXPLORATION", animated: true },
  { id: "e4-5", source: "EXPLORATION", target: "MODELING", animated: true },
  { id: "e5-6", source: "MODELING", target: "EVALUATION", animated: true },
  { id: "e6-7", source: "EVALUATION", target: "DEPLOYMENT", animated: true },
]

export const LabHeader = () => {
  const { state, dispatch } = useLabContext()
  const { activeStages, selectedStage } = state

  const onNodeClick = (_: React.MouseEvent, node: Node) => {
    const stageId = node.id as LabStage
    dispatch({ type: "SET_SELECTED_STAGE", payload: stageId })
  }

  const nodes = useMemo(() => {
    // Determine the currently active stage (latest in pipeline order)
    const ORDERED: LabStage[] = [
      "BUSINESS_UNDERSTANDING",
      "DATA_ACQUISITION",
      "PREPARATION",
      "EXPLORATION",
      "MODELING",
      "EVALUATION",
      "DEPLOYMENT",
    ]
    let currentActiveStage: LabStage | null = null
    for (let i = ORDERED.length - 1; i >= 0; i--) {
      if (activeStages.has(ORDERED[i])) {
        currentActiveStage = ORDERED[i]
        break
      }
    }

    return initialNodes.map((node) => {
      const stageId = node.id as LabStage

      const isSelected = selectedStage === stageId

      let style: React.CSSProperties = {
        width: 150,
        fontSize: "10px",
        border: "1px solid #ddd",
        borderRadius: "4px",
        padding: "8px",
        background: "white",
        cursor: "pointer",
      }

      if (typeof node.style === "object") {
        style = { ...style, ...node.style }
      }

      // E7: Pipeline Node Colors — ACTIVE=blue, COMPLETE=green, PENDING=gray
      if (stageId === currentActiveStage) {
        // ACTIVE stage
        style.background = "#BEE3F8" // blue-100
        style.borderColor = "#3182CE" // blue-500
        style.fontWeight = "bold"
        style.boxShadow = "0 0 0 2px #3182CE"
      } else if (activeStages.has(stageId)) {
        // COMPLETE stage (was active earlier)
        style.background = "#C6F6D5" // green-100
        style.borderColor = "#38A169" // green-500
      } else {
        // PENDING stage
        style.background = "#EDF2F7" // gray-100
        style.borderColor = "#DDD" // gray-300
      }

      // Selection highlight (separate from status)
      if (isSelected && stageId !== currentActiveStage) {
        style.outline = "2px solid #3182CE"
        style.outlineOffset = "2px"
      }

      return {
        ...node,
        style,
      }
    })
  }, [activeStages, selectedStage])

  return (
    <Box h="150px" w="100%" borderBottom="1px solid" borderColor="gray.200">
      <ReactFlow
        nodes={nodes}
        edges={initialEdges}
        onNodeClick={onNodeClick}
        fitView
        attributionPosition="bottom-right"
        proOptions={{ hideAttribution: true }}
        panOnScroll={false}
        zoomOnScroll={false}
        zoomOnPinch={false}
        panOnDrag={false}
        nodesDraggable={false}
        nodesConnectable={false}
      >
        <Background color="#aaa" gap={16} size={1} />
      </ReactFlow>
    </Box>
  )
}
