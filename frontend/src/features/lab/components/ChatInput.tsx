import React, { useState } from 'react';
import { Box, Input, Button, HStack } from '@chakra-ui/react';
import { useLabContext } from '../context/LabContext';
import useCustomToast from '../../../hooks/useCustomToast';

export const ChatInput = () => {
  const { state, isLoading } = useLabContext();
  const [message, setMessage] = useState('');
  const [isSending, setIsSending] = useState(false);
  const { showErrorToast } = useCustomToast();

  const handleSend = async () => {
    if (!message.trim() || !state.sessionId) return;

    setIsSending(true);
    try {
      const response = await fetch(`/api/v1/lab/agent/sessions/${state.sessionId}/message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ content: message }),
      });

      if (!response.ok) {
        throw new Error('Failed to send message');
      }
      
      await response.json();
      
      setMessage('');
    } catch (error) {
      showErrorToast('Error sending message');
    } finally {
      setIsSending(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const isDisabled = !state.isConnected || state.isDone || isLoading;

  return (
    <Box p={4} borderTop="1px solid" borderColor="gray.200" bg="white">
      <HStack>
        <Input
          placeholder={isDisabled ? "Session not active" : "Type a message..."}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={isDisabled}
          bg="gray.50"
        />
        <Button 
          colorScheme="blue" 
          onClick={handleSend}
          loading={isSending}
          disabled={isDisabled || !message.trim()}
        >
          Send
        </Button>
      </HStack>
    </Box>
  );
};
