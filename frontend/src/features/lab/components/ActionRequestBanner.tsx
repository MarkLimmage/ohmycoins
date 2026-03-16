import React from 'react';
import { Box, Button, HStack, Text, VStack, Heading, Icon } from '@chakra-ui/react';
import { FiAlertCircle, FiCheck, FiX, FiEdit } from 'react-icons/fi';
import { ActionRequest } from '../types';
import { useLabContext } from '../context/LabContext';

interface ActionRequestBannerProps {
  request: ActionRequest;
}

export const ActionRequestBanner: React.FC<ActionRequestBannerProps> = ({ request }) => {
  const { sendMessage, dispatch } = useLabContext();

  const handleAction = (option: string) => {
    sendMessage({
      event_type: 'action_response',
      payload: {
        action_id: request.action_id,
        response: option
      }
    });

    // Optimistically clear the pending action
    dispatch({ type: 'CLEAR_ACTION' });
  };

  return (
    <Box 
      p={6} 
      bg="orange.50" 
      borderLeft="4px solid" 
      borderColor="orange.500" 
      borderRadius="md" 
      boxShadow="md" 
      my={4}
      _dark={{ bg: 'orange.900' }}
    >
      <VStack align="start" gap={4}>
        <HStack>
          <Icon as={FiAlertCircle} color="orange.500" boxSize={6} />
          <Heading size="md" color="orange.700" _dark={{ color: 'white' }}>Action Required</Heading>
        </HStack>
        
        <Text fontSize="lg" fontWeight="medium">{request.description}</Text>
        
        <HStack gap={4} pt={2}>
          {request.options.includes('APPROVE') && (
            <Button colorScheme="green" onClick={() => handleAction('APPROVE')}>
               <Icon as={FiCheck} mr={2} />
               Approve
            </Button>
          )}
          
          {request.options.includes('REJECT') && (
            <Button colorScheme="red" variant="outline" onClick={() => handleAction('REJECT')}>
               <Icon as={FiX} mr={2} />
               Reject
            </Button>
          )}

          {request.options.includes('EDIT_BLUEPRINT') && (
            <Button colorScheme="blue" variant="outline" onClick={() => handleAction('EDIT_BLUEPRINT')}>
               <Icon as={FiEdit} mr={2} />
               Edit Blueprint
            </Button>
          )}
        </HStack>
      </VStack>
    </Box>
  );
};
