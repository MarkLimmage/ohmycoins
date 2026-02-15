
import {
  Container,
  Flex,
  Heading,
  Table,
  Tbody,
  Td,
  Th,
  Thead,
  Tr,
  Badge,
  Button,
  useColorModeValue,
  Menu,
  MenuButton,
  MenuItem,
  MenuList,
  Icon,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  FormControl,
  FormLabel,
  Input,
  Select,
  useDisclosure,
  useToast,
  Box,
  Text,
  VStack
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

export const Route = createFileRoute("/_layout/collectors")({
  component: CollectorsPage,
})

function CollectorsPage() {
  const queryClient = useQueryClient()
  const toast = useToast()
  const tableBg = useColorModeValue("white", "gray.800")
  const { isOpen, onOpen, onClose } = useDisclosure()
  
  // Selector Builder State
  const { 
    isOpen: isSelectorOpen, 
    onOpen: onSelectorOpen, 
    onClose: onSelectorClose 
  } = useDisclosure()
  
  // We track which config field we are building a selector for (if multiple)
  // For this sprint, we assume it sets a specific config key
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
      CollectorsService.createCollector({ requestBody: data }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["collectors"] })
      toast({ status: "success", title: "Collector created", duration: 3000 })
      onClose()
      reset()
    },
    onError: (err: ApiError) => {
      toast({
        status: "error",
        title: "Creation failed",
        description: err.body?.detail || err.message,
      })
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, isActive }: { id: string; isActive: boolean }) =>
      CollectorsService.updateCollector({
        id,
        requestBody: { is_active: isActive },
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["collectors"] })
      toast({ status: "success", title: "Collector updated" })
    },
  })

  const runMutation = useMutation({
    mutationFn: (id: string) => CollectorsService.runCollector({ id }),
    onSuccess: () => {
      toast({ status: "info", title: "Run triggered" })
    },
    onError: (err: ApiError) => {
        toast({ status: "error", title: "Run failed", description: err.body?.detail || "Unknown error" })
    }
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => CollectorsService.deleteCollector({ id }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["collectors"] })
      toast({ status: "success", title: "Collector deleted" })
    },
  })

  // --- Form ---
  const { register, handleSubmit, reset, watch, setValue } = useForm<CollectorCreate>()
  const selectedType = watch("type")

  const onSubmit = (data: CollectorCreate) => {
    // Basic defaults
    if (!data.schedule_cron) delete data.schedule_cron
    // Config needs to be an object, react-hook-form might keep it flat or undefined
    if (!data.config) data.config = {}
    
    // Ensure ledger is set
    if (!data.ledger) data.ledger = "glass" 

    createMutation.mutate(data)
  }

  // Helper to inject selector
  const handleSelectorSelect = (selector: string) => {
      // In a real app we'd merge this into the config object
      // For now, we'll assume the form has a helper input for it
      // or we manipulate the config directly
      const currentConfig = watch("config") || {}
      setValue("config", { ...currentConfig, [selectorTarget]: selector })
      toast({ status: "success", title: "Selector Applied", description: selector })
  }

  // --- Render ---
  return (
    <Container maxW="full">
      <Flex py={8} justifyContent="space-between" alignItems="center">
        <Heading size="lg">Data Collectors</Heading>
        <Button leftIcon={<FiPlus />} colorScheme="teal" onClick={onOpen}>
          Add Collector
        </Button>
      </Flex>

      <Table variant="simple" bg={tableBg} shadow="sm">
        <Thead>
          <Tr>
            <Th>Name</Th>
            <Th>Type</Th>
            <Th>Status</Th>
            <Th>Schedule</Th>
            <Th>Last Run</Th>
            <Th>Actions</Th>
          </Tr>
        </Thead>
        <Tbody>
          {isLoading && (
            <Tr>
              <Td colSpan={6} textAlign="center">
                Loading...
              </Td>
            </Tr>
          )}
          {isError && (
             <Tr>
              <Td colSpan={6} textAlign="center" color="red.500">
                Error: {error?.message}
              </Td>
            </Tr>
          )}
          {collectors?.data.map((collector: CollectorPublic) => (
            <Tr key={collector.id}>
              <Td fontWeight="bold">{collector.name}</Td>
              <Td>
                <Badge>{collector.type}</Badge>
              </Td>
              <Td>
                <Badge
                  colorScheme={
                    collector.is_active
                      ? collector.last_status === "error"
                        ? "red"
                        : "green"
                      : "gray"
                  }
                >
                  {collector.is_active ? "Active" : "Paused"}
                </Badge>
              </Td>
              <Td fontSize="sm" fontFamily="monospace">
                {collector.schedule_cron || "Manual"}
              </Td>
              <Td fontSize="sm">
                {collector.last_run_at
                  ? new Date(collector.last_run_at).toLocaleString()
                  : "-"}
              </Td>
              <Td>
                <Menu>
                  <MenuButton as={Button} size="sm" variant="ghost">
                    <Icon as={FiMoreVertical} />
                  </MenuButton>
                  <MenuList>
                    <MenuItem
                      icon={<FiRefreshCw />}
                      onClick={() => runMutation.mutate(collector.id)}
                    >
                      Run Now
                    </MenuItem>
                    <MenuItem
                      icon={collector.is_active ? <FiPause /> : <FiPlay />}
                      onClick={() =>
                        updateMutation.mutate({
                          id: collector.id,
                          isActive: !collector.is_active,
                        })
                      }
                    >
                      {collector.is_active ? "Pause" : "Resume"}
                    </MenuItem>
                    <MenuItem
                      icon={<FiTrash2 />}
                      color="red.500"
                      onClick={() => {
                        if (confirm("Delete this collector?"))
                            deleteMutation.mutate(collector.id)
                      }}
                    >
                      Delete
                    </MenuItem>
                  </MenuList>
                </Menu>
              </Td>
            </Tr>
          ))}
        </Tbody>
      </Table>

      {/* Create Modal */}
      <Modal isOpen={isOpen} onClose={onClose} size="lg">
        <ModalOverlay />
        <ModalContent as="form" onSubmit={handleSubmit(onSubmit)}>
          <ModalHeader>Create New Collector</ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={6}>
            <VStack spacing={4}>
                <FormControl isRequired>
                <FormLabel>Name</FormLabel>
                <Input {...register("name")} placeholder="e.g. CoinGecko Price scraper" />
                </FormControl>

                <FormControl mt={4} isRequired>
                <FormLabel>Type</FormLabel>
                <Select {...register("type")}>
                    <option value="api">API Collector</option>
                    <option value="scraper">Web Scraper</option>
                    <option value="rss">RSS Feed</option>
                </Select>
                </FormControl>
                
                {/* Visual Builder for Scraper */}
                {selectedType === 'scraper' && (
                    <Box w="full" p={4} bg="gray.50" borderRadius="md" border="1px dashed" borderColor="gray.300">
                        <Text fontSize="sm" fontWeight="bold" mb={2}>Scraper Configuration Helper</Text>
                        <Button size="sm" onClick={() => { setSelectorTarget("price_selector"); onSelectorOpen(); }}>
                            Build Selector
                        </Button>
                        <Text fontSize="xs" mt={2} color="gray.500">
                            Current Config: {JSON.stringify(watch("config"))}
                        </Text>
                    </Box>
                )}

                <FormControl mt={4}>
                <FormLabel>Cron Schedule (Optional)</FormLabel>
                <Input
                    {...register("schedule_cron")}
                    placeholder="*/15 * * * *"
                />
                </FormControl>
                
                <FormControl mt={4} isRequired>
                <FormLabel>Ledger</FormLabel>
                <Select {...register("ledger")}>
                    <option value="glass">Glass (Market Data)</option>
                    <option value="human">Human (Social/News)</option>
                    <option value="catalyst">Catalyst (Events)</option>
                    <option value="exchange">Exchange (Order Book)</option>
                </Select>
                </FormControl>
            </VStack>
          </ModalBody>

          <ModalFooter>
            <Button colorScheme="blue" mr={3} type="submit" isLoading={createMutation.isPending}>
              Create
            </Button>
            <Button onClick={onClose}>Cancel</Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
      
      {/* Selector Builder Component */}
      <SelectorBuilder 
        isOpen={isSelectorOpen} 
        onClose={onSelectorClose} 
        onSelect={handleSelectorSelect}
      />
    </Container>
  )
}
