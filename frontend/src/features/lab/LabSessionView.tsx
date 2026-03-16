import React from 'react';
import { VStack, Box, Button } from '@chakra-ui/react';
import { useLabContext } from './context/LabContext';
import { LabGrid } from './components/LabGrid';
import { LabHeader } from './components/LabHeader';
// import { Artifact } from './components/ArtifactViewer'; // Keep if types needed for props, but we are removing props.

interface LabSessionViewProps {}

export const LabSessionView: React.FC<LabSessionViewProps> = () => {
  const { sendMessage } = useLabContext();

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
  );
};
