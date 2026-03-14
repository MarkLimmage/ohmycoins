import { VStack, Text, Box, Spinner, Center } from '@chakra-ui/react';
import { useLabContext } from '../context/LabContext';
import { LabStageRow } from './LabStageRow';

export const LabGrid = () => {
  const { state } = useLabContext();
  const { cells, isConnected, isDone } = state;

  if (cells.length === 0) {
      if (!isConnected && !isDone) {
          return (
            <Center p={10}>
                <Spinner mr={3} />
                <Text>Connecting to Lab Session...</Text>
            </Center>
          )
      }
      return (
        <Center p={10}>
          <Text color="gray.500">No output yet. Start by sending a goal.</Text>
        </Center>
      );
  }

  return (
    <VStack align="stretch" spacing={4} pb={20} w="100%">
      {cells.map((cell) => (
        <LabStageRow key={cell.id} cell={cell} />
      ))}
      {isDone && <Text color="gray.500" textAlign="center" py={4}>Session Finished</Text>}
    </VStack>
  );
};
