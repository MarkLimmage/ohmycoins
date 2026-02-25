import {
  Box,
  SimpleGrid,
  Text,
  Badge,
  Card,
  Heading,
  Table,
  HStack,
  VStack,
  Spinner,
  Alert,
  Icon,
} from "@chakra-ui/react"
import { FiAlertCircle } from "react-icons/fi"
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
import { useCollectorInstances, useCollectorVolume, useCollectorActivity, useCollectorSummaryStats } from "../../hooks/useCollectors"
import type { Collector } from "../../client/types.gen"
import { Checkbox } from "../../components/ui/checkbox"
import { Button } from "../../components/ui/button"
import { useAutoRefresh } from "../../context/AutoRefreshContext"

const StatusBadge = ({ status }: { status?: string }) => {
  let colorScheme = "gray"
  if (status === "running" || status === "active" || status === "enabled") colorScheme = "green"
  if (status === "error" || status === "failed") colorScheme = "red"
  if (status === "stopped" || status === "disabled") colorScheme = "orange"

  return <Badge colorScheme={colorScheme}>{status || "UNKNOWN"}</Badge>
}

export const CollectorHealth = () => {
  const { data: collectors, isLoading, error, refetch } = useCollectorInstances()
  const { data: volumeData, isLoading: volumeLoading, error: volumeError } = useCollectorVolume("24h")
  const { data: activityLogs, isLoading: activityLoading, error: activityError } = useCollectorActivity(50)
  const { data: summaryStats, isLoading: summaryLoading, error: summaryError } = useCollectorSummaryStats()
  const { isEnabled, toggle } = useAutoRefresh()

  if (isLoading) return <Spinner size="xl" />
  if (error) return <Alert.Root status="error"><Icon as={FiAlertCircle} mr={2} />Failed to load collectors</Alert.Root>

  return (
    <Box p={5}>
      <VStack gap={6} align="stretch">
        <HStack justify="space-between">
          <Heading size="lg">Collector Health Dashboard</Heading>
          <HStack gap={4}>
            <Button size="sm" onClick={() => refetch()} loading={isLoading}>
              Refresh Now
            </Button>
            <Checkbox checked={isEnabled} onCheckedChange={() => toggle()}>
              Auto Refresh (30s)
            </Checkbox>
          </HStack>
        </HStack>

        {/* 1. Status Grid */}
        <Box>
          <Heading size="md" mb={4}>Status Grid</Heading>
          <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} gap={4}>
            {collectors?.map((collector: Collector) => (
              <Card.Root key={collector.id} variant="outline">
                <Card.Header pb={2}>
                  <HStack justify="space-between">
                    <Heading size="sm">{collector.name}</Heading>
                    <StatusBadge status={collector.status || (collector.is_enabled ? "active" : "disabled")} />
                  </HStack>
                </Card.Header>
                <Card.Body pt={0}>
                  <Text fontSize="sm" color="gray.500">{collector.plugin_name}</Text>
                  <Text fontSize="xs" mt={2}>Last Run: {collector.last_run_at || "Never"}</Text>
                </Card.Body>
              </Card.Root>
            ))}
            {(!collectors || collectors.length === 0) && (
                 <Text>No collectors found.</Text>
            )}
          </SimpleGrid>
        </Box>

        {/* 1.5 Aggregate Statistics */}
        <Box>
          <Heading size="md" mb={4}>Collection Statistics</Heading>
          {summaryError && (
            <Alert.Root status="error" mb={4}>
              <Icon as={FiAlertCircle} mr={2} />
              Failed to load statistics
            </Alert.Root>
          )}
          {summaryLoading ? (
            <Spinner size="md" />
          ) : (
            <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} gap={4}>
              {(summaryStats || []).map((stat) => (
                <Card.Root key={stat.collector_name} variant="outline">
                  <Card.Header pb={2}>
                    <Heading size="sm">{stat.collector_name}</Heading>
                  </Card.Header>
                  <Card.Body pt={0}>
                    <VStack gap={2} align="start">
                      <Text fontSize="sm">
                        Success Rate: <strong>{stat.uptime_pct.toFixed(1)}%</strong>
                      </Text>
                      <Text fontSize="sm">
                        Total Records: <strong>{stat.total_records}</strong>
                      </Text>
                      <Text fontSize="sm">
                        Avg Duration: <strong>{stat.avg_duration_seconds.toFixed(2)}s</strong>
                      </Text>
                      <Text fontSize="sm">
                        Total Runs: <strong>{stat.total_runs}</strong>
                      </Text>
                    </VStack>
                  </Card.Body>
                </Card.Root>
              ))}
            </SimpleGrid>
          )}
        </Box>

        {/* 2. Volume Chart */}
        <Box>
          <Heading size="md" mb={4}>Items Collected Volume (Last 24 Hours)</Heading>
          {volumeError && (
            <Alert.Root status="error" mb={4}>
              <Icon as={FiAlertCircle} mr={2} />
              Failed to load volume data
            </Alert.Root>
          )}
          {volumeLoading ? (
            <Spinner size="md" />
          ) : (
            <Box height="400px">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={volumeData || []}
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
          )}
        </Box>

        {/* 3. Activity Stream */}
        <Box>
          <Heading size="md" mb={4}>Recent Activity</Heading>
          {activityError && (
            <Alert.Root status="error" mb={4}>
              <Icon as={FiAlertCircle} mr={2} />
              Failed to load activity logs
            </Alert.Root>
          )}
          {activityLoading ? (
            <Spinner size="md" />
          ) : (
            <Card.Root variant="outline">
              <Table.Root variant="outline" size="sm">
                <Table.Header>
                  <Table.Row>
                    <Table.ColumnHeader>Timestamp</Table.ColumnHeader>
                    <Table.ColumnHeader>Collector</Table.ColumnHeader>
                    <Table.ColumnHeader>Status</Table.ColumnHeader>
                    <Table.ColumnHeader textAlign="right">Items</Table.ColumnHeader>
                    <Table.ColumnHeader textAlign="right">Duration (s)</Table.ColumnHeader>
                  </Table.Row>
                </Table.Header>
                <Table.Body>
                  {(activityLogs || []).map((log) => (
                    <Table.Row key={log.id}>
                      <Table.Cell>{log.timestamp}</Table.Cell>
                      <Table.Cell>{log.collector}</Table.Cell>
                      <Table.Cell>
                        <Badge colorScheme={log.status === "success" ? "green" : log.status === "error" ? "red" : "yellow"}>
                          {log.status}
                        </Badge>
                      </Table.Cell>
                      <Table.Cell textAlign="right">{log.items}</Table.Cell>
                      <Table.Cell textAlign="right">{log.duration.toFixed(2)}</Table.Cell>
                    </Table.Row>
                  ))}
                </Table.Body>
              </Table.Root>
            </Card.Root>
          )}
        </Box>

      </VStack>
    </Box>
  )
}
