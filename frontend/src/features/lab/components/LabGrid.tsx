import { Grid, GridItem, Center, Spinner, Text } from '@chakra-ui/react';
import { useLabContext } from '../context/LabContext';
import { DialoguePanel } from './DialoguePanel';
import { ActivityTracker } from './ActivityTracker';
import { StageOutputs } from './StageOutputs';

export const LabGrid = () => {
  const { state, isLoading } = useLabContext();
  const { activeStages, dialogueMessages } = state;

  // We want to show grid as soon as we connect or if we have content
  const hasContent = activeStages.size > 0 || dialogueMessages.length > 0;
  
  if (!hasContent && isLoading) {
      return (
        <Center p={10} h="100%">
            <Spinner mr={3} />
            <Text>Rehydrating Session...</Text>
        </Center>
      )
  }

  return (
    <Grid
      h="100%"
      templateColumns="350px 1fr 300px" // Left | Center | Right
      gap={4}
      p={2}
    >
      {/* Left Column: Dialogue */}
      <GridItem bg="white" borderRadius="md" shadow="sm" overflow="hidden" h="100%" border="1px solid" borderColor="gray.200">
         <DialoguePanel />
      </GridItem>

      {/* Center Column: Activity Tracker */}
      <GridItem bg="white" borderRadius="md" shadow="sm" overflow="hidden" h="100%" border="1px solid" borderColor="gray.200">
         <ActivityTracker />
      </GridItem>

      {/* Right Column: Stage Outputs */}
      <GridItem bg="white" borderRadius="md" shadow="sm" overflow="hidden" h="100%" border="1px solid" borderColor="gray.200">
         <StageOutputs />
      </GridItem>
    </Grid>
  );
};
