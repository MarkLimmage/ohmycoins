import { VStack, Center, Spinner, Text } from '@chakra-ui/react';
import { useLabContext } from '../context/LabContext';
import { LabStageRow } from './LabStageRow';
import { ActionRequestBanner } from './ActionRequestBanner';
import { LabStage } from '../types';

const ORDERED_STAGES: LabStage[] = [
  'BUSINESS_UNDERSTANDING',
  'DATA_ACQUISITION',
  'PREPARATION',
  'EXPLORATION',
  'MODELING',
  'EVALUATION',
  'DEPLOYMENT'
];

const STAGE_LABELS: Record<LabStage, string> = {
  'BUSINESS_UNDERSTANDING': '1. Business Understanding',
  'DATA_ACQUISITION': '2. Data Acquisition',
  'PREPARATION': '3. Preparation',
  'EXPLORATION': '4. Exploration',
  'MODELING': '5. Modeling',
  'EVALUATION': '6. Evaluation',
  'DEPLOYMENT': '7. Deployment',
};

export const LabGrid = () => {
  const { state, isLoading } = useLabContext();
  const { stages, isConnected, isDone, pendingAction } = state;

  // Determine active stage (last one with cells or explicitly set)
  // For now, let's say the last stage that has cells is the "active" context, 
  // but really the backend dictates the "current" stage via events.
  // We can use the last stage with cells as a proxy if explicit active stage is missing.
  
  // Or better, we visualize all stages.
  
  const hasContent = Object.values(stages).some(cells => cells.length > 0);
  const hasActivity = hasContent || !!pendingAction || state.activeStages.size > 0;

  if (!hasActivity && isLoading) {
      return (
        <Center p={10}>
            <Spinner mr={3} />
            <Text>Rehydrating Session...</Text>
        </Center>
      )
  }

  if (!hasActivity && !isConnected && !isDone) {
      return (
        <Center p={10}>
             {/* Show spinner if we expect connection, otherwise just empty state */}
            <Spinner mr={3} />
            <Text>Connecting to Lab Session...</Text>
        </Center>
      )
  }

  if (!hasActivity && isDone) {
      return (
        <Center p={10}>
          <Text color="gray.500">Session Finished with no content.</Text>
        </Center>
      );
  }

  return (
    <VStack align="stretch" gap={6} pb={20} w="100%">
      
      {/* Action Request Banner at top if urgent, or interleaved? 
          Usually modal or top banner. Top of grid is good. */}
      {pendingAction && (
        <ActionRequestBanner request={pendingAction} />
      )}

      {ORDERED_STAGES.map((stage) => {
        const cells = stages[stage] || [];
        // isActive logic: 
        // 1. If we have pending action, maybe none is "active" in terms of processing, but the stage with action is relevant.
        // 2. The last stage with activity might be active.
        // 3. Or use state.activeStages Set if I implemented it correctly in reducer.
        
        // Let's use state.activeStages
        const isActive = state.activeStages.has(stage);

        return (
          <LabStageRow 
            key={stage} 
            stage={stage} 
            cells={cells} 
            isActive={isActive} 
            label={STAGE_LABELS[stage]}
          />
        );
      })}
      
      {isDone && (
        <Center py={8}>
            <Text color="gray.500">Session Completed</Text>
        </Center>
      )}
    </VStack>
  );
};
