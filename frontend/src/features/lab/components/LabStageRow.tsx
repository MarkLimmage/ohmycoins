import React, { useEffect, useState } from 'react';
import { Box, VStack, Heading, SimpleGrid, Icon, SlideFade, Collapse, HStack } from '@chakra-ui/react';
import { LabStage, LabCell } from '../types';
import { CellRenderer } from './CellRenderer';
import { FiCheckCircle, FiCircle, FiLoader } from 'react-icons/fi';

export interface LabStageRowProps {
  stage: LabStage;
  cells: LabCell[];
  isActive: boolean;
  label: string;
}

export const LabStageRow: React.FC<LabStageRowProps> = ({ stage, cells, isActive, label }) => {
  const [isOpen, setIsOpen] = useState(false);
  
  useEffect(() => {
    if (isActive || cells.length > 0) {
        setIsOpen(true);
    }
  }, [isActive, cells.length]);

  if (!isOpen && !isActive && cells.length === 0) {
      return (
          <HStack p={2} opacity={0.4} _hover={{ opacity: 1, cursor: 'pointer' }} onClick={() => setIsOpen(true)}>
             <Icon as={FiCircle} color="gray.300" />
             <Heading size="xs" color="gray.500">{label}</Heading>
          </HStack>
      )
  }

  return (
    <Box 
        p={4} 
        borderLeftWidth="4px" 
        borderColor={isActive ? 'blue.500' : (cells.length > 0 ? 'green.500' : 'gray.200')} 
        bg={isActive ? 'blue.50' : 'transparent'}
        _dark={{ bg: isActive ? 'blue.900' : 'transparent' }}
        transition="all 0.3s"
        borderRadius="md"
        mb={4}
    >
      <VStack align="start" spacing={4} w="100%">
        <HStack spacing={2} pb={2} borderBottomWidth={cells.length > 0 ? "1px" : "0px"} w="100%">
            {isActive ? (
                <Icon as={FiLoader} animation="spin 2s linear infinite" color="blue.500" />
            ) : (
                <Icon as={cells.length > 0 ? FiCheckCircle : FiCircle} color={cells.length > 0 ? 'green.500' : 'gray.400'} />
            )}
            <Heading size="sm" color={isActive ? 'blue.600' : 'gray.700'} _dark={{ color: 'gray.200' }}>
              {label}
            </Heading>
        </HStack>

        <SimpleGrid columns={1} spacing={4} w="100%">
          {cells.map((cell) => (
            <CellRenderer key={cell.id} cell={cell} />
          ))}
        </SimpleGrid>
      </VStack>
      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </Box>
  );
};
