import React from 'react';
import { Box, Code, Image, Text, Badge, VStack } from '@chakra-ui/react';
import Plot from 'react-plotly.js';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { LabCell, LabMimeType } from '../types';
import { BlueprintCard } from './BlueprintCard';
import { Tearsheet } from './Tearsheet';

interface CellRendererProps {
  cell: LabCell;
}

export const CellRenderer: React.FC<CellRendererProps> = ({ cell }) => {
  const { type, content, metadata } = cell;

  const renderContent = () => {
    switch (type) {
      case 'text/markdown':
        return (
          <Box className="markdown-body" fontSize="sm">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {typeof content === 'string' ? content : JSON.stringify(content)}
            </ReactMarkdown>
          </Box>
        );

      case 'application/vnd.plotly.v1+json':
        try {
            const plotData = typeof content === 'string' ? JSON.parse(content) : content;
            return (
              <Plot
                data={plotData.data}
                layout={{...plotData.layout, autosize: true}}
                style={{ width: '100%', height: '100%' }}
                useResizeHandler={true}
              />
            );
        } catch (e) {
            return <Text color="red.500">Error rendering plot: {String(e)}</Text>
        }

      case 'application/json+blueprint':
        return <BlueprintCard data={content} />;

      case 'application/json+tearsheet':
        return <Tearsheet data={content} />;

      case 'image/png':
        return (
          <Image 
            src={`data:image/png;base64,${content}`} 
            alt="Generated Plot" 
            maxH="400px" 
            objectFit="contain" 
          />
        );

      default:
        return (
          <VStack align="start">
             <Text color="orange.500">Unknown Mime-Type: {type}</Text>
             <Code p={2} w="100%" overflowX="auto">
                {JSON.stringify(content, null, 2)}
             </Code>
          </VStack>
        );
    }
  };

  return (
    <Box 
      p={4} 
      borderWidth="1px" 
      borderRadius="md" 
      bg="white" 
      shadow="sm" 
      width="100%"
      position="relative"
    >
      {/* E7: Cached Parquet Badge */}
      {metadata?.source === 'cache' && (
        <Badge position="absolute" top={2} right={2} colorScheme="green">
          Cached
        </Badge>
      )}
      
      {/* E6: Model Discarded UI */}
      {metadata?.lifecycle === 'discarded' && (
        <Box 
            position="absolute" 
            top={0} left={0} right={0} bottom={0} 
            bg="rgba(0,0,0,0.05)" 
            zIndex={1} 
            pointerEvents="none"
            display="flex"
            alignItems="center"
            justifyContent="center"
        >
            <Badge colorScheme="red" fontSize="xl" transform="rotate(-15deg)">
                DISCARDED
            </Badge>
        </Box>
      )}

      {renderContent()}
    </Box>
  );
};
