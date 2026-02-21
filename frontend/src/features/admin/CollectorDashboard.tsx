import { 
  Button, 
  Card, 
  Container, 
  Flex, 
  Heading, 
  Table, 
  Text, 
  Badge,
  IconButton,
  HStack,
  Box
} from "@chakra-ui/react"
import { FiPlay, FiPause, FiTrash2, FiEdit, FiActivity } from "react-icons/fi"
import { useCollectors, useCollectorStats } from "./hooks"
import { CollectorInstance } from "./types"
import { CollectorPluginForm } from "./CollectorForm"
import { useState } from "react"
import { DialogBody, DialogContent, DialogHeader, DialogRoot, DialogTrigger, DialogCloseTrigger } from "@/components/ui/dialog"
import { Tooltip } from "@/components/ui/tooltip"
import { LineChart, Line, ResponsiveContainer } from 'recharts'

// Sub-component for Sparkline
const ThroughputSparkline = ({ collectorId }: { collectorId: string }) => {
  const { data: stats } = useCollectorStats(collectorId);
  
  if (!stats?.throughput || stats.throughput.length === 0) 
      return <Text fontSize="xs" color="gray.400">No data</Text>;
  
  return (
    <Box h="40px" w="120px">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={stats.throughput}>
          <Line 
            type="monotone" 
            dataKey="items_collected" 
            stroke="#8884d8" 
            strokeWidth={2} 
            dot={false} 
          />
        </LineChart>
      </ResponsiveContainer>
    </Box>
  );
};

// Sub-component for Health Indicator
const HealthIndicator = ({ collectorId }: { collectorId: string }) => {
    const { data: stats } = useCollectorStats(collectorId);

    if (!stats) return <Badge colorScheme="gray">Unknown</Badge>;

    return (
        <Badge colorScheme={stats.status === 'success' ? 'green' : 'red'}>
            {stats.status === 'success' ? 'Healthy' : 'Error'}
        </Badge>
    );
};

export const CollectorDashboard = () => {
  const { instances, plugins, deleteInstance, toggleInstance } = useCollectors()
  const [isDialogOpen, setIsDialogOpen] = useState(false)

  if (instances.isLoading || plugins.isLoading) {
    return <Text>Loading collectors...</Text>
  }

  const handleDelete = (id: string) => {
    if (confirm("Are you sure you want to delete this collector?")) {
      deleteInstance.mutate(id)
    }
  }

  const handleToggle = (instance: CollectorInstance) => {
    toggleInstance.mutate({ id: instance.id, is_active: !instance.is_active })
  }

  return (
    <Container maxW="container.xl" py={8}>
      <Flex justify="space-between" align="center" mb={8}>
        <Heading size="lg">Data Collectors</Heading>
        <DialogRoot open={isDialogOpen} onOpenChange={(e) => setIsDialogOpen(e.open)}>
          <DialogTrigger asChild>
            <Button colorScheme="blue" onClick={() => setIsDialogOpen(true)}>
              + Add Collector
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>Add New Collector</DialogHeader>
            <DialogCloseTrigger />
            <DialogBody>
              <CollectorPluginForm 
                plugins={plugins.data || []} 
                onCancel={() => setIsDialogOpen(false)} 
                onSuccess={() => setIsDialogOpen(false)}
              /> 
            </DialogBody>
          </DialogContent>
        </DialogRoot>
      </Flex>

      <Card.Root>
        <Card.Body p={0}>
          <Table.Root>
            <Table.Header>
              <Table.Row>
                <Table.ColumnHeader>Name</Table.ColumnHeader>
                <Table.ColumnHeader>Plugin</Table.ColumnHeader>
                <Table.ColumnHeader>Active Streams</Table.ColumnHeader>
                <Table.ColumnHeader>Health</Table.ColumnHeader>
                <Table.ColumnHeader>Throughput (items/min)</Table.ColumnHeader>
                <Table.ColumnHeader>Last Run</Table.ColumnHeader>
                <Table.ColumnHeader textAlign="right">Actions</Table.ColumnHeader>
              </Table.Row>
            </Table.Header>
            <Table.Body>
              {instances.data?.map((instance) => (
                <Table.Row key={instance.id}>
                  <Table.Cell fontWeight="medium">{instance.name}</Table.Cell>
                  <Table.Cell>
                    <Badge variant="subtle" colorScheme="purple">
                      {plugins.data?.find(p => p.id === instance.plugin_id)?.name || instance.plugin_id}
                    </Badge>
                  </Table.Cell>
                  <Table.Cell>
                    <Badge 
                      colorScheme={instance.is_active ? 'green' : 'gray'}
                    >
                      {instance.is_active ? 'Running' : 'Stopped'}
                    </Badge>
                  </Table.Cell>
                  <Table.Cell>
                      {/* Health Indicator - using useCollectorStats */}
                      <HealthIndicator collectorId={instance.id} />
                  </Table.Cell>
                  <Table.Cell>
                      {/* Sparkline */}
                      <ThroughputSparkline collectorId={instance.id} />
                  </Table.Cell>
                  <Table.Cell color="gray.500">
                    {instance.last_run ? new Date(instance.last_run).toLocaleString() : 'Never'}
                  </Table.Cell>
                  <Table.Cell textAlign="right">
                    <Flex justify="flex-end" gap={2}>
                      <Tooltip content={instance.is_active ? "Pause" : "Start"}>
                        <IconButton 
                          aria-label={instance.is_active ? "Pause" : "Start"}
                          colorScheme={instance.is_active ? "orange" : "green"}
                          size="sm"
                          onClick={() => handleToggle(instance)}
                        >
                          {instance.is_active ? <FiPause /> : <FiPlay />}
                        </IconButton>
                      </Tooltip>

                      <Tooltip content="Run Now">
                        <IconButton 
                          aria-label="Run Now"
                          colorScheme="blue"
                          size="sm"
                          onClick={() => console.log("Run now triggered", instance.id)} 
                        >
                          <FiActivity />
                        </IconButton>
                      </Tooltip>

                      <Tooltip content="Edit">
                        <IconButton 
                           aria-label="Edit"
                           colorScheme="gray"
                           size="sm"
                           onClick={() => alert("Edit functionality coming soon")}
                        >
                          <FiEdit />
                        </IconButton>
                      </Tooltip>

                      <Tooltip content="Delete">
                        <IconButton 
                          aria-label="Delete"
                          colorScheme="red"
                          size="sm"
                          onClick={() => handleDelete(instance.id)}
                        >
                          <FiTrash2 />
                        </IconButton>
                      </Tooltip>
                    </Flex>
                  </Table.Cell>
                </Table.Row>
              ))}
              {instances.data?.length === 0 && (
                <Table.Row>
                  <Table.Cell colSpan={6} textAlign="center" py={8} color="gray.500">
                    No collectors configured. Click "Add Collector" to get started.
                  </Table.Cell>
                </Table.Row>
              )}
            </Table.Body>
          </Table.Root>
        </Card.Body>
      </Card.Root>
    </Container>
  )
}
