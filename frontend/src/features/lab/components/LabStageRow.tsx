import React from 'react';
import Plotly from 'plotly.js-dist-min';
import createPlotlyComponent from 'react-plotly.js/factory';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Box, Code, Text, VStack, Badge, HStack } from '@chakra-ui/react';
import { LabCell } from '../context/LabContext';

// Use factory to avoid large bundle size if possible, or just default import if lazy loading is not set up
const Plot = createPlotlyComponent(Plotly);

interface LabStageRowProps {
  cell: LabCell;
}

export const LabStageRow: React.FC<LabStageRowProps> = ({ cell }) => {
  const { type, content, metadata, status, timestamp } = cell;

  const renderContent = () => {
    if (type === 'plotly') {
      try {
        const plotData = typeof content === 'string' ? JSON.parse(content) : content;
        return (
          <Box w="100%" h="400px">
            <Plot
              data={plotData.data}
              layout={{ ...plotData.layout, autosize: true }}
              config={{ responsive: true }}
              style={{ width: '100%', height: '100%' }}
              useResizeHandler={true}
            />
          </Box>
        );
      } catch (e: any) {
        return <Text color="red.500">Error parsing Plotly JSON: {e.message}</Text>;
      }
    }

    if (type === 'markdown' || type === 'thought') {
      return (
        <Box className="markdown-body" fontSize="sm">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
        </Box>
      );
    }

    if (type === 'code' || type === 'tool' || type === 'blueprint') {
      return (
        <Code display="block" whiteSpace="pre" p={2} borderRadius="md" w="100%" overflowX="auto">
          {content}
        </Code>
      );
    }

    if (type === 'output' || type === 'result' || type === 'error') {
        const isError = type === 'error' || metadata?.error || status === 'failed';
        return (
            <Code 
                display="block" 
                whiteSpace="pre-wrap" 
                p={2} 
                borderRadius="md" 
                w="100%" 
                color={isError ? "red.500" : "inherit"}
                bg={isError ? "red.50" : "gray.50"}
                _dark={{ bg: isError ? "red.900" : "gray.800" }}
            >
                {content}
            </Code>
        )
    }

    return <Text>{content}</Text>;
  };

  const getBadgeColor = () => {
      switch (type) {
          case 'thought': return 'blue';
          case 'tool': return 'purple';
          case 'result': return metadata?.error ? 'red' : 'green';
          case 'plotly': return 'orange';
          case 'blueprint': return 'cyan';
          case 'metric': return 'teal';
          case 'error': return 'red';
          default: return 'gray';
      }
  }

  return (
    <Box 
        borderWidth="1px" 
        borderRadius="lg" 
        p={4} 
        m={2} 
        bg="white" 
        _dark={{ bg: 'gray.800' }} 
        shadow="sm"
        borderLeft="4px solid"
        borderLeftColor={`${getBadgeColor()}.400`}
    >
      <VStack align="stretch" gap={2}>
        <HStack justify="space-between">
            <Badge colorScheme={getBadgeColor()}>{type.toUpperCase()}</Badge>
            {timestamp && <Text fontSize="xs" color="gray.500">{new Date(timestamp).toLocaleTimeString()}</Text>}
        </HStack>
        <Box>
            {renderContent()}
        </Box>
      </VStack>
    </Box>
  );
};
