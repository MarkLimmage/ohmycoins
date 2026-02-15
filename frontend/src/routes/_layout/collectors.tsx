
import {
  Container,
  Flex,
  Heading,
  Table,
  Badge,
  Button,
  Icon,
  Box,
  Text,
  VStack,
  chakra,
  Input
} from "@chakra-ui/react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { FiMoreVertical, FiPlay, FiPause, FiRefreshCw, FiTrash2, FiPlus } from "react-icons/fi"
import { useForm } from "react-hook-form"
import { useState } from "react"

// Import generated client
import { CollectorsService } from "../../client"
import type { CollectorCreate, CollectorPublic } from "../../client"
import { ApiError } from "../../client/core/ApiError"
import { SelectorBuilder } from "../../components/SelectorBuilder"
import {
  DialogRoot,
  DialogContent,
  DialogHeader,
  DialogCloseTrigger,
  DialogBody,
  DialogFooter,
} from "../../components/ui/dialog"
import { Field } from "../../components/ui/field"
import {
  MenuRoot,
  MenuTrigger,
  MenuContent,
  MenuItem,
} from "../../components/ui/menu"
import { toaster } from "../../components/ui/toaster"

export const Route = createFileRoute("/_layout/collectors")({
  component: CollectorsPage,
})

function CollectorsPage() {
  const queryClient = useQueryClient()
  
  // Create Dialog State
  const [isCreateOpen, setCreateOpen] = useState(false)
  const onCreateOpen = () => setCreateOpen(true)
  const onCreateClose = () => setCreateOpen(false)
  
  // Selector Builder State
  const [isSelectorOpen, setSelectorOpen] = useState(false)
  
  const [selectorTarget, setSelectorTarget] = useState<string>("price_selector")

  // --- Queries ---
  const {
    data: collectors,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ["collectors"],
    queryFn: () => CollectorsService.readCollectors({ skip: 0, limit: 100 }),
  })

  // --- Mutations ---
  const createMutation = useMutation({
    mutationFn: (data: CollectorCreate) =>
      CollectorsService.createCollectorEndpoint({ requestBody: data }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["collectors"] })
      toaster.create({ title: "Collector created", type: "success" })
      onCreateClose()
      reset()
    },
    onError: (err: ApiError) => {
      toaster.create({
        type: "error",
        title: "Creation failed",
        description: (err.body as any)?.detail || err.message,
      })
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, isActive }: { id: string; isActive: boolean }) =>
      CollectorsService.updateCollectorEndpoint({
        collectorId: id,
        requestBody: { is_active: isActive },
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["collectors"] })
      toaster.create({ title: "Collector updated", type: "success" })
    },
  })

  const runMutation = useMutation({
    mutationFn: (name: string) => CollectorsService.triggerCollector({ collectorName: name }),
    onSuccess: () => {
      toaster.create({ title: "Run triggered", type: "info" })
    },
    onError: (err: ApiError) => {
      toaster.create({ title: "Run failed", description: (err.body as any)?.detail || "Unknown error", type: "error" })
    }
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => CollectorsService.deleteCollectorEndpoint({ collectorId: id }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["collectors"] })
      toaster.create({ title: "Collector deleted", type: "success" })
    },
  })

  // --- Form ---
  const { register, handleSubmit, reset, watch, setValue } = useForm<CollectorCreate>()
  const selectedType = watch("type")

  const onSubmit = (data: CollectorCreate) => {
    // Clean up schedule if empty
    if (!data.schedule) delete data.schedule
    if (!data.config) data.config = {}
    
    createMutation.mutate(data)
  }

  const handleSelectorSelect = (selector: string) => {
      const currentConfig = watch("config") ?? {}
      setValue("config", { ...(currentConfig as Record<string, unknown>), [selectorTarget]: selector })
      toaster.create({ title: "Selector Applied", description: selector, type: "success" })
  }

  return (
    <Container maxW="full">
      <Flex py={8} justifyContent="space-between" alignItems="center">
        <Heading size="lg">Data Collectors</Heading>
        <Button onClick={onCreateOpen} colorPalette="teal">
          <FiPlus /> Add Collector
        </Button>
      </Flex>

      <Table.Root variant="outline" bg="white" _dark={{ bg: "gray.800" }} shadow="sm">
        <Table.Header>
          <Table.Row>
            <Table.ColumnHeader>Name</Table.ColumnHeader>
            <Table.ColumnHeader>Type</Table.ColumnHeader>
            <Table.ColumnHeader>Status</Table.ColumnHeader>
            <Table.ColumnHeader>Schedule</Table.ColumnHeader>
            <Table.ColumnHeader>Last Run</Table.ColumnHeader>
            <Table.ColumnHeader>Actions</Table.ColumnHeader>
          </Table.Row>
        </Table.Header>
        <Table.Body>
          {isLoading && (
            <Table.Row>
              <Table.Cell colSpan={6} textAlign="center">
                Loading...
              </Table.Cell>
            </Table.Row>
          )}
          {isError && (
             <Table.Row>
              <Table.Cell colSpan={6} textAlign="center" color="red.500">
                Error: {error?.message}
              </Table.Cell>
            </Table.Row>
          )}
          {collectors?.data.map((collector: CollectorPublic) => (
            <Table.Row key={collector.id}>
              <Table.Cell fontWeight="bold">{collector.name}</Table.Cell>
              <Table.Cell>
                <Badge>{collector.type}</Badge>
              </Table.Cell>
              <Table.Cell>
                <Badge
                  colorPalette={
                    collector.is_active
                      ? collector.last_status === "error"
                        ? "red"
                        : "green"
                      : "gray"
                  }
                >
                  {collector.is_active ? "Active" : "Paused"}
                </Badge>
              </Table.Cell>
              <Table.Cell fontSize="sm" fontFamily="monospace">
                {collector.schedule || "Manual"}
              </Table.Cell>
              <Table.Cell fontSize="sm">
                {collector.last_run_at
                  ? new Date(collector.last_run_at).toLocaleString()
                  : "-"}
              </Table.Cell>
              <Table.Cell>
                <MenuRoot>
                  <MenuTrigger asChild>
                    <Button size="sm" variant="ghost">
                        <Icon as={FiMoreVertical} />
                    </Button>
                  </MenuTrigger>
                  <MenuContent>
                    <MenuItem
                      value="run"
                      onClick={() => runMutation.mutate(collector.name)}
                    >
                      <FiRefreshCw /> Run Now
                    </MenuItem>
                    <MenuItem
                      value="toggle"
                      onClick={() =>
                        updateMutation.mutate({
                          id: collector.id,
                          isActive: !collector.is_active,
                        })
                      }
                    >
                      {collector.is_active ? <FiPause /> : <FiPlay />}
                      {collector.is_active ? "Pause" : "Resume"}
                    </MenuItem>
                    <MenuItem
                      value="delete"
                      color="red.500"
                      onClick={() => {
                        if (confirm("Delete this collector?"))
                            deleteMutation.mutate(collector.id)
                      }}
                    >
                      <FiTrash2 /> Delete
                    </MenuItem>
                  </MenuContent>
                </MenuRoot>
              </Table.Cell>
            </Table.Row>
          ))}
        </Table.Body>
      </Table.Root>

      {/* Create Modal */}
      <DialogRoot open={isCreateOpen} onOpenChange={(e) => setCreateOpen(e.open)} size="lg">
        <DialogContent>
          <DialogHeader>Create New Collector</DialogHeader>
          <DialogCloseTrigger />
          <DialogBody>
            <form id="create-collector-form" onSubmit={handleSubmit(onSubmit)}>
            <VStack gap={4} align="stretch">
                <Field label="Name" required>
                    <Input {...register("name")} placeholder="e.g. CoinGecko Price scraper" />
                </Field>

                <Field label="Type" required>
                    <chakra.select 
                        {...register("type")} 
                        height="10" 
                        width="full" 
                        borderRadius="md" 
                        borderWidth="1px" 
                        borderColor="inherit"
                        px={3}
                    >
                        <option value="api">API Collector</option>
                        <option value="scraper">Web Scraper</option>
                        <option value="rss">RSS Feed</option>
                    </chakra.select>
                </Field>
                
                {selectedType === 'scraper' && (
                    <Box w="full" p={4} bg="gray.50" borderRadius="md" border="1px dashed" borderColor="gray.300">
                        <Text fontSize="sm" fontWeight="bold" mb={2}>Scraper Configuration Helper</Text>
                        <Button size="sm" onClick={() => { setSelectorTarget("price_selector"); setSelectorOpen(true); }}>
                            Build Selector
                        </Button>
                        <Text fontSize="xs" mt={2} color="gray.500">
                            Current Config: {JSON.stringify(watch("config"))}
                        </Text>
                    </Box>
                )}

                <Field label="Cron Schedule (Optional)" helperText="Format: */15 * * * *">
                    <Input
                        {...register("schedule")}
                        placeholder="*/15 * * * *"
                    />
                </Field>
            </VStack>
            </form>
          </DialogBody>

          <DialogFooter>
            <Button variant="ghost" mr={3} onClick={onCreateClose}>Cancel</Button>
            <Button colorPalette="blue" type="submit" form="create-collector-form" loading={createMutation.isPending}>
              Create
            </Button>
          </DialogFooter>
        </DialogContent>
      </DialogRoot>
      
      {/* Selector Builder Component */}
      <SelectorBuilder 
        isOpen={isSelectorOpen} 
        onClose={() => setSelectorOpen(false)} 
        onSelect={handleSelectorSelect}
      />
    </Container>
  )
}
