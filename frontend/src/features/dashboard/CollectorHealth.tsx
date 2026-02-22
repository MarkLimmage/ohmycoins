import {
  Box,
  SimpleGrid,
  Text,
  Badge,
  Card,
  CardHeader,
  CardBody,
  Heading,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  HStack,
  VStack,
  Spinner,
  Alert,
  AlertIcon,
} from "@chakra-ui/react"
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts"
import { useCollectorInstances } from "../../hooks/useCollectors"
import type { Collector } from "../../client/types.gen"

// Mock Data for Activity Stream
const MOCK_ACTIVITY_LOGS = [
  { id: 1, timestamp: "2026-02-22 10:00:00", collector: "Glass-ETH", status: "SUCCESS", items: 154, duration: "1.2s" },
  { id: 2, timestamp: "2026-02-22 10:05:00", collector: "Human-Reddit", status: "SUCCESS", items: 45, duration: "2.5s" },
  { id: 3, timestamp: "2026-02-22 10:10:00", collector: "Catalyst-SEC", status: "FAILURE", items: 0, duration: "0.5s" },
  { id: 4, timestamp: "2026-02-22 10:15:00", collector: "Exchange-Binance", status: "SUCCESS", items: 1200, duration: "0.8s" },
  { id: 5, timestamp: "2026-02-22 10:20:00", collector: "Glass-SOL", status: "SUCCESS", items: 300, duration: "1.1s" },
]

// Mock Data for Volume Chart (Stacked Bar)
const MOCK_VOLUME_DATA = [
  { time: "08:00", Glass: 400, Human: 240, Catalyst: 100, Exchange: 2400 },
  { time: "09:00", Glass: 300, Human: 139, Catalyst: 200, Exchange: 2210 },
  { time: "10:00", Glass: 200, Human: 980, Catalyst: 200, Exchange: 2290 },
  { time: "11:00", Glass: 278, Human: 390, Catalyst: 300, Exchange: 2000 },
  { time: "12:00", Glass: 189, Human: 480, Catalyst: 150, Exchange: 2181 },
  { time: "13:00", Glass: 239, Human: 380, Catalyst: 100, Exchange: 2500 },
  { time: "14:00", Glass: 349, Human: 430, Catalyst: 210, Exchange: 2100 },
]

const StatusBadge = ({ status }: { status?: string }) => {
  let colorScheme = "gray"
  if (status === "running" || status === "active" || status === "enabled") colorScheme = "green"
  if (status === "error" || status === "failed") colorScheme = "red"
  if (status === "stopped" || status === "disabled") colorScheme = "orange"

  return <Badge colorScheme={colorScheme}>{status || "UNKNOWN"}</Badge>
}

export const CollectorHealth = () => {
  const { data: collectors, isLoading, error } = useCollectorInstances()

  if (isLoading) return <Spinner size="xl" />
  if (error) return <Alert status="error"><AlertIcon />Failed to load collectors</Alert>

  return (
    <Box p={5}>
      <VStack gap={6} align="stretch">
        <Heading size="lg">Collector Health Dashboard</Heading>

        {/* 1. Status Grid */}
        <Box>
          <Heading size="md" mb={4}>Status Grid</Heading>
          <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} gap={4}>
            {collectors?.map((collector: Collector) => (
              <Card key={collector.id} variant="outline">
                <CardHeader pb={2}>
                  <HStack justify="space-between">
                    <Heading size="sm">{collector.name}</Heading>
                    <StatusBadge status={collector.status || (collector.is_enabled ? "active" : "disabled")} />
                  </HStack>
                </CardHeader>
                <CardBody pt={0}>
                  <Text fontSize="sm" color="gray.500">{collector.plugin_name}</Text>
                  <Text fontSize="xs" mt={2}>Last Run: {collector.last_run_at || "Never"}</Text>
                </CardBody>
              </Card>
            ))}
            {(!collectors || collectors.length === 0) && (
                 <Text>No collectors found.</Text>
            )}
          </SimpleGrid>
        </Box>

        {/* 2. Volume Chart */}
        <Box height="400px">
          <Heading size="md" mb={4}>Items Collected Volume (Last 7 Hours)</Heading>
           <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={MOCK_VOLUME_DATA}
              margin={{
                top: 20,
                right: 30,
                left: 20,
                bottom: 5,
              }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="Glass" stackId="a" fill="#8884d8" />
              <Bar dataKey="Human" stackId="a" fill="#82ca9d" />
              <Bar dataKey="Catalyst" stackId="a" fill="#ffc658" />
              <Bar dataKey="Exchange" stackId="a" fill="#ff7300" />
            </BarChart>
          </ResponsiveContainer>
        </Box>

        {/* 3. Activity Stream */}
        <Box>
          <Heading size="md" mb={4}>Recent Activity</Heading>
          <Card variant="outline">
            <Table variant="simple" size="sm">
              <Thead>
                <Tr>
                  <Th>Timestamp</Th>
                  <Th>Collector</Th>
                  <Th>Status</Th>
                  <Th isNumeric>Items</Th>
                  <Th isNumeric>Duration</Th>
                </Tr>
              </Thead>
              <Tbody>
                {MOCK_ACTIVITY_LOGS.map((log) => (
                  <Tr key={log.id}>
                    <Td>{log.timestamp}</Td>
                    <Td>{log.collector}</Td>
                    <Td>
                      <Badge colorScheme={log.status === "SUCCESS" ? "green" : "red"}>{log.status}</Badge>
                    </Td>
                    <Td isNumeric>{log.items}</Td>
                    <Td isNumeric>{log.duration}</Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
          </Card>
        </Box>

      </VStack>
    </Box>
  )
}
