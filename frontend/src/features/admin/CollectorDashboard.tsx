import { 
  Button, 
  Card, 
  Container, 
  Flex, 
  Heading, 
  Table, 
  Text, 
  Badge,
  IconButton
} from "@chakra-ui/react"
import { FiPlay, FiPause, FiTrash2 } from "react-icons/fi"
import { useCollectors } from "./hooks"
import { CollectorInstance } from "./types"
import { CollectorPluginForm } from "./CollectorForm"
import { useState } from "react"
import { DialogBody, DialogContent, DialogHeader, DialogRoot, DialogTrigger, DialogCloseTrigger } from "@/components/ui/dialog"
import { Tooltip } from "@/components/ui/tooltip"

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
                <Table.ColumnHeader>Status</Table.ColumnHeader>
                <Table.ColumnHeader>Last Run</Table.ColumnHeader>
                <Table.ColumnHeader>Success/Error</Table.ColumnHeader>
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
                      colorScheme={instance.status === 'success' ? 'green' : instance.status === 'failed' ? 'red' : 'gray'}
                    >
                      {instance.status}
                    </Badge>
                  </Table.Cell>
                  <Table.Cell color="gray.500">
                    {instance.last_run ? new Date(instance.last_run).toLocaleString() : 'Never'}
                  </Table.Cell>
                  <Table.Cell>
                    <Text color="green.500" as="span">{instance.success_count}</Text>
                    {' / '}
                    <Text color="red.500" as="span">{instance.error_count}</Text>
                  </Table.Cell>
                  <Table.Cell textAlign="right">
                    <Flex justify="flex-end" gap={2}>
                      <Tooltip content={instance.is_active ? "Pause" : "Resume"}>
                        <IconButton 
                          aria-label={instance.is_active ? "Pause" : "Resume"}
                          size="sm" 
                          variant="ghost"
                          colorScheme={instance.is_active ? "orange" : "green"}
                          onClick={() => handleToggle(instance)}
                        >
                          {instance.is_active ? <FiPause /> : <FiPlay />}
                        </IconButton>
                      </Tooltip>
                      <Tooltip content="Delete">
                        <IconButton 
                          aria-label="Delete"
                          size="sm" 
                          variant="ghost" 
                          colorScheme="red"
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
