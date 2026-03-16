import React, { useMemo } from 'react';
import ReactFlow, { Background, Node, Edge, Position } from 'reactflow';
import 'reactflow/dist/style.css';
import { Box } from '@chakra-ui/react';
import { useLabContext } from '../context/LabContext';
import { LabStage } from '../types';

const initialNodes: Node[] = [
  { id: 'BUSINESS_UNDERSTANDING', position: { x: 0, y: 50 }, data: { label: 'Business Understanding' }, type: 'input', sourcePosition: Position.Right, targetPosition: Position.Left },
  { id: 'DATA_ACQUISITION', position: { x: 200, y: 50 }, data: { label: 'Data Acquisition' }, type: 'default', sourcePosition: Position.Right, targetPosition: Position.Left },
  { id: 'PREPARATION', position: { x: 400, y: 50 }, data: { label: 'Preparation' }, type: 'default', sourcePosition: Position.Right, targetPosition: Position.Left },
  { id: 'EXPLORATION', position: { x: 600, y: 50 }, data: { label: 'Exploration' }, type: 'default', sourcePosition: Position.Right, targetPosition: Position.Left },
  { id: 'MODELING', position: { x: 800, y: 50 }, data: { label: 'Modeling' }, type: 'default', sourcePosition: Position.Right, targetPosition: Position.Left },
  { id: 'EVALUATION', position: { x: 1000, y: 50 }, data: { label: 'Evaluation' }, type: 'default', sourcePosition: Position.Right, targetPosition: Position.Left },
  { id: 'DEPLOYMENT', position: { x: 1200, y: 50 }, data: { label: 'Deployment' }, type: 'output', sourcePosition: Position.Right, targetPosition: Position.Left },
];

const initialEdges: Edge[] = [
  { id: 'e1-2', source: 'BUSINESS_UNDERSTANDING', target: 'DATA_ACQUISITION', animated: true },
  { id: 'e2-3', source: 'DATA_ACQUISITION', target: 'PREPARATION', animated: true },
  { id: 'e3-4', source: 'PREPARATION', target: 'EXPLORATION', animated: true },
  { id: 'e4-5', source: 'EXPLORATION', target: 'MODELING', animated: true },
  { id: 'e5-6', source: 'MODELING', target: 'EVALUATION', animated: true },
  { id: 'e6-7', source: 'EVALUATION', target: 'DEPLOYMENT', animated: true },
];

export const LabHeader = () => {
  const { state } = useLabContext();
  const { stages, activeStages } = state;

  const nodes = useMemo(() => {
    return initialNodes.map((node) => {
      const stageId = node.id as LabStage;
      // Determine status from state
      let status = 'PENDING';
      const isActive = activeStages.has(stageId);
      const hasCells = stages[stageId] && stages[stageId].length > 0;

      if (isActive) status = 'ACTIVE';
      else if (hasCells) status = 'COMPLETE';

      let style: React.CSSProperties = { width: 150, fontSize: '10px' };
      
      if (status === 'COMPLETE') style = { ...style, background: '#68D391', color: 'black' }; // Green
      else if (status === 'ACTIVE') style = { ...style, background: '#F6E05E', color: 'black', border: '2px solid orange' }; // Yellow
      else if (status === 'FAILED') style = { ...style, background: '#FC8181', color: 'white' }; // Red
      else if (status === 'PENDING') style = { ...style, background: '#E2E8F0', color: 'gray' }; // Gray

      return {
        ...node,
        style: { ...node.style, ...style },
      };
    });
  }, [stages, activeStages]);

  return (
    <Box h="150px" w="100%" borderBottom="1px solid" borderColor="gray.200">
      <ReactFlow 
        nodes={nodes} 
        edges={initialEdges} 
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
  );
};
