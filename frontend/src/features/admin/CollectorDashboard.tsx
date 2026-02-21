import { 
  Button, 
  Container, 
  Flex, 
  Heading, 
  Text, 
  SimpleGrid,
  Box
} from "@chakra-ui/react"
import { useCollectors } from "./hooks"
import { CollectorInstance } from "./types"
import { CollectorPluginForm } from "./CollectorForm"
import { CollectorCard } from "./CollectorCard"
import { useState } from "react"
import { DialogBody, DialogContent, DialogHeader, DialogRoot, DialogTrigger, DialogCloseTrigger } from "@/components/ui/dialog"

export const CollectorDashboard = () => {
  const { instances, plugins, deleteInstance, toggleInstance } = useCollectors()
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [selectedInstance, setSelectedInstance] = useState<CollectorInstance | undefined>(undefined)

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

  const handleEdit = (instance: CollectorInstance) => {
    setSelectedInstance(instance)
    setIsDialogOpen(true)
  }

  return (
    <Container maxW="container.xl" py={8}>
      <Flex justify="space-between" align="center" mb={8}>
        <Heading size="lg">Data Collectors</Heading>
        <DialogRoot open={isDialogOpen} onOpenChange={(e) => {
          setIsDialogOpen(e.open)
          if (!e.open) setSelectedInstance(undefined)
        }}>
          <DialogTrigger asChild>
            <Button colorScheme="blue" onClick={() => setIsDialogOpen(true)}>
              + Add Collector
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>{selectedInstance ? "Edit Collector" : "Add New Collector"}</DialogHeader>
            <DialogCloseTrigger />
            <DialogBody>
              <CollectorPluginForm 
                plugins={plugins.data || []} 
                initialValues={selectedInstance}
                onCancel={() => setIsDialogOpen(false)} 
                onSuccess={() => setIsDialogOpen(false)}
              /> 
            </DialogBody>
          </DialogContent>
        </DialogRoot>
      </Flex> 

      {instances.data?.length === 0 ? (
        <Box textAlign="center" py={10} bg="gray.50" borderRadius="md">
           <Text color="gray.500">No collectors configured. Click "Add Collector" to get started.</Text>
        </Box>
      ) : (
        <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} gap={6}>
            {instances.data?.map((instance) => (
                <CollectorCard 
                    key={instance.id} 
                    instance={instance}
                    pluginName={plugins.data?.find(p => p.id === instance.plugin_id)?.name || instance.plugin_id}
                    onEdit={() => handleEdit(instance)}
                    onToggle={() => handleToggle(instance)}
                    onDelete={() => handleDelete(instance.id)}
                />
            ))}
        </SimpleGrid>
      )}
    </Container>
  )
}

