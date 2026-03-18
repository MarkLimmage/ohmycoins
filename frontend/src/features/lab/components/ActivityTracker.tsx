import { useMemo } from 'react';
import { Box, VStack, Text, HStack, Icon, Spinner, Heading, Accordion } from '@chakra-ui/react';
import { FiCheckCircle, FiCircle, FiAlertCircle } from 'react-icons/fi';
import { useLabContext } from '../context/LabContext';
import { LabStage, ActivityItem } from '../types';

const STAGE_LABELS: Record<LabStage, string> = {
  'BUSINESS_UNDERSTANDING': '1. Business Understanding',
  'DATA_ACQUISITION': '2. Data Acquisition',
  'PREPARATION': '3. Preparation',
  'EXPLORATION': '4. Exploration',
  'MODELING': '5. Modeling',
  'EVALUATION': '6. Evaluation',
  'DEPLOYMENT': '7. Deployment',
};

const ORDERED_STAGES: LabStage[] = [
  'BUSINESS_UNDERSTANDING',
  'DATA_ACQUISITION',
  'PREPARATION',
  'EXPLORATION',
  'MODELING',
  'EVALUATION',
  'DEPLOYMENT'
];

const StatusIcon = ({ status }: { status: ActivityItem['status'] }) => {
  switch (status) {
    case 'completed':
      return <Icon as={FiCheckCircle} color="green.500" />;
    case 'active':
      return <Spinner size="xs" color="blue.500" />;
    case 'failed':
      return <Icon as={FiAlertCircle} color="red.500" />;
    default:
      return <Icon as={FiCircle} color="gray.300" />;
  }
};

const ActivityItemRow = ({ item }: { item: ActivityItem }) => (
  <HStack gap={3} py={1} pl={2}>
    <StatusIcon status={item.status} />
    <Text fontSize="sm" color={item.status === 'completed' ? 'gray.500' : 'gray.800'}>
      {item.description}
    </Text>
  </HStack>
);

export const ActivityTracker = () => {
  const { state } = useLabContext();
  const { activityItems, activeStages } = state;

  const groupedItems = useMemo(() => {
    const groups: Record<string, ActivityItem[]> = {};
    
    // Initialize groups for all stages
    ORDERED_STAGES.forEach(stage => {
        groups[stage] = [];
    });

    activityItems.forEach(item => {
      if (!groups[item.stage]) {
        groups[item.stage] = [];
      }
      groups[item.stage].push(item);
    });
    return groups;
  }, [activityItems]);

  // Determine which accordion items are open (active stages)
  const activeStageValues = ORDERED_STAGES.filter(stage => activeStages.has(stage));
  const defaultValue = activeStageValues.length > 0 ? activeStageValues : [ORDERED_STAGES[0]];

  return (
    <Box h="100%" bg="gray.50" borderRight="1px solid" borderColor="gray.200" overflowY="auto">
      <Box p={3} borderBottom="1px solid" borderColor="gray.200" bg="white">
        <Heading size="sm">Activity Tracker</Heading>
      </Box>

      <Accordion.Root multiple defaultValue={defaultValue} collapsible>
        {ORDERED_STAGES.map((stage) => {
          const items = groupedItems[stage] || [];
          const isActive = activeStages.has(stage);
          
          return (
            <Accordion.Item key={stage} value={stage} border="none">
              <h2>
                <Accordion.ItemTrigger _expanded={{ bg: 'blue.50', color: 'blue.700' }}>
                  <Box flex="1" textAlign="left" fontWeight={isActive ? 'bold' : 'normal'}>
                    {STAGE_LABELS[stage]}
                  </Box>
                  <Accordion.ItemIndicator />
                </Accordion.ItemTrigger>
              </h2>
              <Accordion.ItemContent pb={4} bg="white">
                <VStack alignItems="stretch" gap={1}>
                  {items.length === 0 ? (
                    <Text fontSize="xs" color="gray.400" pl={2}>No tasks tracked</Text>
                  ) : (
                    items.map((item, idx) => (
                      <ActivityItemRow key={item.id || idx} item={item} />
                    ))
                  )}
                </VStack>
              </Accordion.ItemContent>
            </Accordion.Item>
          );
        })}
      </Accordion.Root>
    </Box>
  );
};
