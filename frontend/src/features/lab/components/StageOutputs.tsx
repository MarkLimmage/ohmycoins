import { useMemo } from 'react';
import { Box, VStack, Heading, Text, Center } from '@chakra-ui/react';
import { useLabContext } from '../context/LabContext';
// import { CellRenderer } from './CellRenderer'; // Existing component
// Wait, CellRenderer needs to be updated? No, mission says "DO NOT remove existing components (CellRenderer... Reuse them)"
// But CellRenderer references LabCell which I updated. LabCell has id, stage, type, content, timestamp, metadata.
// I should verify CellRenderer import. It is in the same directory.
import { CellRenderer } from './CellRenderer';
import { LabStage } from '../types';

const STAGE_LABELS: Record<LabStage, string> = {
  'BUSINESS_UNDERSTANDING': 'Business Understanding',
  'DATA_ACQUISITION': 'Data Acquisition',
  'PREPARATION': 'Preparation',
  'EXPLORATION': 'Exploration',
  'MODELING': 'Modeling',
  'EVALUATION': 'Evaluation',
  'DEPLOYMENT': 'Deployment',
};

const ORDERED_STAGES: LabStage[] = [
  'BUSINESS_UNDERSTANDING',
  'DATA_ACQUISITION',
  'PREPARATION',
  'EXPLORATION',
  'MODELING',
  'EVALUATION',
  'DEPLOYMENT'
];

export const StageOutputs = () => {
  const { state } = useLabContext();
  const { stageOutputs, selectedStage, activeStages } = state;

  // Determine which stage to show
  const activeStage = useMemo(() => {
    if (selectedStage) return selectedStage;
    
    // Default: first active stage in reverse order (presumably latest)
    for (let i = ORDERED_STAGES.length - 1; i >= 0; i--) {
        if (activeStages.has(ORDERED_STAGES[i])) {
            return ORDERED_STAGES[i];
        }
    }
    
    return 'BUSINESS_UNDERSTANDING'; // Fallback
  }, [selectedStage, activeStages]);

  const outputs = stageOutputs[activeStage] || [];

  return (
    <Box h="100%" bg="white" overflowY="auto" p={4}>
      <Box pb={4} borderBottom="1px solid" borderColor="gray.100" mb={4}>
         <Heading size="md" mb={1}>{STAGE_LABELS[activeStage]}</Heading>
         <Text fontSize="sm" color="gray.500">
            {outputs.length} output{outputs.length !== 1 ? 's' : ''} generated
         </Text>
      </Box>
      
      {outputs.length === 0 ? (
        <Center h="200px" bg="gray.50" borderRadius="md" border="1px dashed" borderColor="gray.300">
            <Text color="gray.400">No outputs for this stage yet.</Text>
        </Center>
      ) : (
        <VStack gap={6} alignItems="stretch">
            {outputs.map((cell) => (
                <CellRenderer key={cell.id} cell={cell} />
            ))}
        </VStack>
      )}
    </Box>
  );
};
