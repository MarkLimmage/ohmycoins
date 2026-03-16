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
      <VStack align="start" spacing={4}>
        <HStack>
          <Icon as={FiAlertCircle} color="orange.500" boxSize={6} />
          <Heading size="md" color="orange.700" _dark={{ color: 'white' }}>Action Required</Heading>
        </HStack>
        
        <Text fontSize="lg" fontWeight="medium">{request.description}</Text>
        
        <HStack spacing={4} pt={2}>
          {request.options.includes('APPROVE') && (
            <Button leftIcon={<FiCheck />} colorScheme="green" onClick={() => handleAction('APPROVE')}>
              Approve
            </Button>
          )}
          
          {request.options.includes('REJECT') && (
            <Button leftIcon={<FiX />} colorScheme="red" variant="outline" onClick={() => handleAction('REJECT')}>
              Reject
            </Button>
          )}

          {request.options.includes('EDIT_BLUEPRINT') && (
            <Button leftIcon={<FiEdit />} colorScheme="blue" variant="outline" onClick={() => handleAction('EDIT_BLUEPRINT')}>
              Edit Blueprint
            </Button>
          )}
        </HStack>
      </VStack>
    </Box>
  );
};
