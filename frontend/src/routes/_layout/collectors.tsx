import {
  Badge,
  Box,
  Button,
  Container,
  Flex,
  Heading,
  HStack,
  IconButton,
  Table,
  Text,
  useDisclosure, 
  VStack,
} from "@chakra-ui/react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { formatDistanceToNow } from "date-fns"
import { useState } from "react"
import { FaPause, FaPlay, FaSync } from "react-icons/fa"

// --- Mock Types & Service (Replace with actual API later) ---

export type CollectorStatus = "active" | "paused" | "error"
export type CollectorType = "api" | "scraper"

export interface Collector {
  id: string
  name: string
  type: CollectorType
  status: CollectorStatus
  lastRun: string | null
  successRate: number
  intervalSeconds: number
  config: Record<string, unknown>
}

// Mock Data
const MOCK_COLLECTORS: Collector[] = [
  {
    id: "1",
    name: "DefiLlama TVL",
    type: "api",
    status: "active",
    lastRun: new Date(Date.now() - 1000 * 60 * 5).toISOString(), // 5 mins ago
    successRate: 99.5,
    intervalSeconds: 300,
    config: { endpoint: "https://api.llama.fi/tvl" },
  },
  {
    id: "2",
    name: "Coingecko Price",
    type: "api",
    status: "paused",
    lastRun: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(), // 2 hours ago
    successRate: 98.2,
    intervalSeconds: 60,
    config: { ids: ["bitcoin", "ethereum"] },
  },
  {
    id: "3",
    name: "CryptoNews Scraper",
    type: "scraper",
    status: "error",
    lastRun: new Date(Date.now() - 1000 * 60 * 15).toISOString(),
    successRate: 45.0,
    intervalSeconds: 1800,
    config: { url: "https://cryptonews.com", selector: ".news-item" },
  },
]

const CollectorsService = {
  getCollectors: async (): Promise<Collector[]> => {
    // Simulate API delay
    await new Promise((resolve) => setTimeout(resolve, 500))
    return [...MOCK_COLLECTORS]
  },
  runCollector: async (id: string): Promise<void> => {
    console.log(`Running collector ${id}`)
    await new Promise((resolve) => setTimeout(resolve, 500))
  },
  toggleCollector: async (id: string, currentStatus: CollectorStatus): Promise<void> => {
    console.log(`Toggling collector ${id} from ${currentStatus}`)
    await new Promise((resolve) => setTimeout(resolve, 500))
  },
}

// --- Route Definition ---

export const Route = createFileRoute("/_layout/collectors")({
  component: CollectorsAdmin,
})

// --- Components ---

function CollectorsAdmin() {
  const queryClient = useQueryClient()

  // Fetch Collectors
  const { data: collectors, isLoading } = useQuery({
    queryKey: ["collectors"],
    queryFn: CollectorsService.getCollectors,
  })

  // Mutations
  const runMutation = useMutation({
    mutationFn: CollectorsService.runCollector,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["collectors"] })
    },
  })

  const toggleMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: CollectorStatus }) =>
      CollectorsService.toggleCollector(id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["collectors"] })
    },
  })

  const handleRun = (id: string) => {
    runMutation.mutate(id)
  }

  const handleToggle = (id: string, status: CollectorStatus) => {
    toggleMutation.mutate({ id, status })
  }

  return (
    <Container maxW="full">
      <Flex justify="space-between" align="center" pt={12}>
        <Heading size="lg">Collector Management</Heading>
        <Button colorPalette="teal" size="sm">
          + New Collector
        </Button>
      </Flex>

      <Box mt={8}> {/* Use standard Box for spacing */}
        {isLoading ? (
          <Text>Loading collectors...</Text>
        ) : (
          <Table.Root size="sm" striped>
            <Table.Header>
              <Table.Row>
                <Table.ColumnHeader>Name</Table.ColumnHeader>
                <Table.ColumnHeader>Type</Table.ColumnHeader>
                <Table.ColumnHeader>Status</Table.ColumnHeader>
                <Table.ColumnHeader>Last Run</Table.ColumnHeader>
                <Table.ColumnHeader>Success Rate</Table.ColumnHeader>
                <Table.ColumnHeader>Actions</Table.ColumnHeader>
              </Table.Row>
            </Table.Header>
            <Table.Body>
              {collectors?.map((collector) => (
                <Table.Row key={collector.id}>
                  <Table.Cell fontWeight="medium">{collector.name}</Table.Cell>
                  <Table.Cell>
                    <Badge colorPalette={collector.type === "api" ? "blue" : "purple"}>
                      {collector.type.toUpperCase()}
                    </Badge>
                  </Table.Cell>
                  <Table.Cell>
                    <Badge
                      colorPalette={
                        collector.status === "active"
                          ? "green"
                          : collector.status === "paused"
                            ? "yellow"
                            : "red"
                      }
                    >
                      {collector.status.toUpperCase()}
                    </Badge>
                  </Table.Cell>
                  <Table.Cell>
                    {collector.lastRun
                      ? formatDistanceToNow(new Date(collector.lastRun), {
                          addSuffix: true,
                        })
                      : "Never"}
                  </Table.Cell>
                  <Table.Cell>
                    <Text
                      color={
                        collector.successRate >= 90
                          ? "green.500"
                          : collector.successRate >= 70
                            ? "yellow.500"
                            : "red.500"
                      }
                      fontWeight="bold"
                    >
                      {collector.successRate}%
                    </Text>
                  </Table.Cell>
                  <Table.Cell>
                    <HStack gap={2}>
                      <IconButton
                        aria-label="Run Now"
                        size="sm"
                        colorPalette="blue"
                        loading={runMutation.isPending}
                        onClick={() => handleRun(collector.id)}
                      >
                        <FaPlay />
                      </IconButton>
                      <IconButton
                        aria-label={
                          collector.status === "paused" ? "Resume" : "Pause"
                        }
                        size="sm"
                        colorPalette={
                          collector.status === "paused" ? "green" : "orange"
                        }
                        loading={toggleMutation.isPending}
                        onClick={() =>
                          handleToggle(collector.id, collector.status)
                        }
                      >
                        {collector.status === "paused" ? (
                          <FaPlay />
                        ) : (
                          <FaPause />
                        )}
                      </IconButton>
                    </HStack>
                  </Table.Cell>
                </Table.Row>
              ))}
            </Table.Body>
          </Table.Root>
        )}
      </Box>
    </Container>
  )
}
