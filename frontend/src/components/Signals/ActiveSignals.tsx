import {
  Badge,
  Box,
  Card,
  Heading,
  Table,
  Text,
  Stack,
  HStack,
  Icon,
  Spinner,
} from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { FiTrendingDown, FiTrendingUp, FiMinus, FiActivity } from "react-icons/fi"

import { OpenAPI } from "@/client" // Import OpenAPI to access BASE URL

interface Signal {
  id: number
  type: string
  asset: string
  strength: number
  generated_at: string
  source: string
  context: Record<string, any>
}

const fetchActiveSignals = async (): Promise<Signal[]> => {
  // Use OpenAPI.BASE if set, otherwise default (though it should be set)
  const baseUrl = OpenAPI.BASE || "http://localhost:8040/api/v1"
  const url = `${baseUrl}/mock/signals/active`
  const token = localStorage.getItem("access_token")
  
  const response = await fetch(url, {
      headers: {
          'Authorization': `Bearer ${token}`
      }
  })
  if (!response.ok) {
    throw new Error("Failed to fetch active signals")
  }
  return response.json()
}

export function ActiveSignals() {
  const { data: signals, isLoading } = useQuery({
    queryFn: fetchActiveSignals,
    queryKey: ["signals", "active"],
  })

  if (isLoading) {
    return (
        <Card.Root>
            <Card.Body>
                <Stack align="center" justify="center" h="100px">
                    <Spinner size="lg" />
                    <Text>Loading signals...</Text>
                </Stack>
            </Card.Body>
        </Card.Root>
    )
  }

  return (
    <Card.Root>
      <Card.Header pb={2}>
        <Heading size="md" display="flex" alignItems="center" gap={2}>
            <Icon as={FiActivity} />
            Active Signals
        </Heading>
      </Card.Header>
      <Card.Body>
        {signals && signals.length > 0 ? (
          <Table.Root size="sm" variant="outline">
            <Table.Header>
              <Table.Row>
                <Table.ColumnHeader>Asset</Table.ColumnHeader>
                <Table.ColumnHeader>Type</Table.ColumnHeader>
                <Table.ColumnHeader>Strength</Table.ColumnHeader>
                <Table.ColumnHeader>Source</Table.ColumnHeader>
                <Table.ColumnHeader>Generated</Table.ColumnHeader>
              </Table.Row>
            </Table.Header>
            <Table.Body>
              {signals.map((signal) => (
                <Table.Row key={signal.id}>
                  <Table.Cell fontWeight="bold">{signal.asset}</Table.Cell>
                  <Table.Cell>
                    <Badge
                        colorScheme={
                            signal.type === "buy" ? "green" :
                            signal.type === "sell" ? "red" : "gray"
                        }
                    >
                        {signal.type === "buy" && <Icon as={FiTrendingUp} mr={1} />}
                        {signal.type === "sell" && <Icon as={FiTrendingDown} mr={1} />}
                        {signal.type === "neutral" && <Icon as={FiMinus} mr={1} />}
                        {signal.type.toUpperCase()}
                    </Badge>
                  </Table.Cell>
                  <Table.Cell>{(signal.strength * 100).toFixed(0)}%</Table.Cell>
                  <Table.Cell fontSize="xs" color="gray.500">{signal.source}</Table.Cell>
                  <Table.Cell fontSize="xs" color="gray.500">
                    {new Date(signal.generated_at).toLocaleTimeString()}
                  </Table.Cell>
                </Table.Row>
              ))}
            </Table.Body>
          </Table.Root>
        ) : (
          <Box p={4} textAlign="center" color="gray.500">
            No active signals detected.
          </Box>
        )}
      </Card.Body>
    </Card.Root>
  )
}
