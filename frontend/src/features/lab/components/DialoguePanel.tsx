import { useEffect, useRef } from 'react';
import { Box, Text, VStack, Flex, Icon } from '@chakra-ui/react';
import { useLabContext } from '../context/LabContext';
import { ActionRequestBanner } from './ActionRequestBanner';
import { ChatInput } from './ChatInput';
import { FiUser, FiCpu, FiAlertTriangle } from 'react-icons/fi';
import { DialogueMessage } from '../types';

const MessageBubble = ({ message }: { message: DialogueMessage }) => {
  const isAgent = message.type === 'agent';
  const isUser = message.type === 'user';
  const isError = message.type === 'error';
  
  const align = isUser ? 'flex-end' : 'flex-start';
  const bg = isUser ? 'gray.100' : isError ? 'red.50' : 'blue.50';
  const color = isUser ? 'gray.800' : isError ? 'red.800' : 'blue.900';
  const borderColor = isError ? 'red.200' : isAgent ? 'blue.200' : 'transparent';
  const icon = isUser ? FiUser : isError ? FiAlertTriangle : FiCpu;

  return (
    <Flex w="100%" justify={align} mb={2}>
      <Box 
        maxW="85%" 
        p={3} 
        borderRadius="lg" 
        bg={bg} 
        color={color}
        border="1px solid"
        borderColor={borderColor}
        boxShadow="sm"
      >
        <Flex align="center" mb={1} gap={2}>
            <Icon as={icon} size="sm" opacity={0.7} />
            <Text fontSize="xs" fontWeight="bold" opacity={0.7}>
                {isUser ? 'You' : isError ? 'System Error' : 'System Agent'}
            </Text>
        </Flex>
        <Text whiteSpace="pre-wrap" fontSize="sm">{message.content}</Text>
      </Box>
    </Flex>
  );
};

export const DialoguePanel = () => {
  const { state } = useLabContext();
  const { dialogueMessages, isConnected, pendingAction } = state;
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [dialogueMessages, pendingAction]);

  return (
    <Flex direction="column" h="100%" bg="white" borderRight="1px solid" borderColor="gray.200">
      {/* Header */}
      <Box p={3} borderBottom="1px solid" borderColor="gray.200" bg="gray.50">
        <Flex justify="space-between" align="center">
            <Text fontWeight="bold" fontSize="sm">Dialogue Stream</Text>
            <Flex align="center" gap={2}>
                <Box w={2} h={2} borderRadius="full" bg={isConnected ? 'green.500' : 'red.500'} />
                <Text fontSize="xs" color="gray.500">
                    {isConnected ? 'WS: LIVE' : 'WS: DISCONNECTED'}
                </Text>
            </Flex>
        </Flex>
      </Box>

      {/* Messages Area */}
      <VStack 
        flex={1} 
        overflowY="auto" 
        p={4} 
        alignItems="stretch" 
        gap={4}
        css={{
            '&::-webkit-scrollbar': { width: '4px' },
            '&::-webkit-scrollbar-track': { width: '6px' },
            '&::-webkit-scrollbar-thumb': { background: '#CBD5E0', borderRadius: '24px' },
        }}
      >
        {dialogueMessages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}

        {/* Pending Action Card */}
        {pendingAction && (
             <Box animation="pulse">
                <ActionRequestBanner request={pendingAction} />
             </Box>
        )}
        
        <div ref={messagesEndRef} />
      </VStack>

      {/* Input Area */}
      <ChatInput />
    </Flex>
  );
};
