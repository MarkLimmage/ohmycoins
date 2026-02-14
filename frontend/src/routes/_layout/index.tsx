import {
  Badge,
  Box,
  Button,
  Card,
  Container,
  Flex,
  Grid,
  Heading,
  Icon,
  Stat,
  Table,
  Tabs,
  Text,
} from "@chakra-ui/react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { FiActivity, FiPause, FiPlay, FiTrendingUp } from "react-icons/fi"

import { FloorService, MockService, PnlService } from "@/client"
import useAuth from "@/hooks/useAuth"

export const Route = createFileRoute("/_layout/")({
  component: Dashboard,
})

function Dashboard() {
  const { user: currentUser } = useAuth()
  const queryClient = useQueryClient()

  // 1. Fetch Live P&L (Real)
  const { data: livePnl, isLoading: liveLoading } = useQuery({
    queryFn: () => PnlService.getPnlSummary({}),
    queryKey: ["pnl", "summary", "live"],
  })

  // 2. Fetch Paper P&L (Mock/Simulated for Sprint 2.26 visibility)
  const { data: paperPnl, isLoading: paperLoading } = useQuery({
    queryFn: () =>
      MockService.getMockLedgerData({
        ledgerType: "algorithm",
        state: "success",
      }),
    queryKey: ["pnl", "summary", "paper"],
  })

  // 3. Fetch Active Agents (Using PnL by Algo as proxy for list)
  const { data: agents, isLoading: agentsLoading } = useQuery({
    queryFn: () => PnlService.getPnlByAlgorithm({}),
    queryKey: ["pnl", "by-algo"],
  })

  // Mutations for Control Panel
  const pauseMutation = useMutation({
    mutationFn: (id: string) =>
      FloorService.pauseAlgorithm({ algorithmId: id }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["pnl"] })
      // Ideally we refresh status here
    },
  })

  const resumeMutation = useMutation({
    mutationFn: (id: string) =>
      FloorService.resumeAlgorithm({ algorithmId: id }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["pnl"] })
    },
  })

  return (
    <Container maxW="full" py={8}>
      {/* Header */}
      <Flex justify="space-between" align="center" mb={8}>
        <Box>
          <Heading size="lg">Mission Control</Heading>
          <Text color="gray.500">
            Welcome back, {currentUser?.full_name || currentUser?.email}
          </Text>
        </Box>
        <Badge
          colorScheme="purple"
          fontSize="md"
          px={3}
          py={1}
          borderRadius="full"
        >
          BETA: ACTIVE
        </Badge>
      </Flex>

      <Tabs.Root defaultValue="live">
        <Tabs.List mb={6}>
          <Tabs.Trigger value="live">
            <Icon as={FiActivity} mr={2} />
            Live Beta
          </Tabs.Trigger>
          <Tabs.Trigger value="paper">
            <Icon as={FiTrendingUp} mr={2} />
            Paper Simulations
          </Tabs.Trigger>
        </Tabs.List>

        {/* LIVE TAB */}
        <Tabs.Content value="live">
          <Grid
            templateColumns={{ base: "1fr", md: "repeat(3, 1fr)" }}
            gap={6}
            mb={8}
          >
            <StatCard
              label="Total Realized P&L"
              value={livePnl?.realized_pnl}
              type="currency"
              isLoading={liveLoading}
            />
            <StatCard
              label="Unrealized P&L"
              value={livePnl?.unrealized_pnl}
              type="currency"
              isLoading={liveLoading}
            />
            <StatCard
              label="Win Rate"
              value={livePnl?.win_rate}
              type="percent"
              isLoading={liveLoading}
            />
          </Grid>

          <Heading size="md" mb={4}>
            Active Agents Control
          </Heading>
          <Card.Root variant="elevated">
            <Card.Body>
              {agentsLoading ? (
                <Text>Loading agents...</Text>
              ) : (
                <Table.Root size="md">
                  <Table.Header>
                    <Table.Row>
                      <Table.ColumnHeader>Agent ID</Table.ColumnHeader>
                      <Table.ColumnHeader textAlign="right">
                        Realized P&L
                      </Table.ColumnHeader>
                      <Table.ColumnHeader textAlign="center">
                        Actions
                      </Table.ColumnHeader>
                    </Table.Row>
                  </Table.Header>
                  <Table.Body>
                    {agents?.map((agent) => (
                      <Table.Row key={agent.algorithm_id}>
                        <Table.Cell
                          fontWeight="medium"
                          fontSize="xs"
                          color="gray.500"
                        >
                          {agent.algorithm_id}
                        </Table.Cell>
                        <Table.Cell
                          textAlign="right"
                          color={
                            agent.realized_pnl >= 0 ? "green.500" : "red.500"
                          }
                        >
                          ${agent.realized_pnl?.toFixed(2)}
                        </Table.Cell>
                        <Table.Cell textAlign="center">
                          <Flex justify="center" gap={2}>
                            <Button
                              size="xs"
                              colorScheme="yellow"
                              onClick={() =>
                                pauseMutation.mutate(agent.algorithm_id)
                              }
                              loading={pauseMutation.isPending}
                            >
                              <Icon as={FiPause} mr={1} /> Pause
                            </Button>
                            <Button
                              size="xs"
                              colorScheme="green"
                              onClick={() =>
                                resumeMutation.mutate(agent.algorithm_id)
                              }
                              loading={resumeMutation.isPending}
                            >
                              <Icon as={FiPlay} mr={1} /> Resume
                            </Button>
                          </Flex>
                        </Table.Cell>
                      </Table.Row>
                    ))}
                    {agents?.length === 0 && (
                      <Table.Row>
                        <Table.Cell
                          colSpan={3}
                          textAlign="center"
                          py={4}
                          color="gray.500"
                        >
                          No active agents found on the floor.
                        </Table.Cell>
                      </Table.Row>
                    )}
                  </Table.Body>
                </Table.Root>
              )}
            </Card.Body>
          </Card.Root>
        </Tabs.Content>

        {/* PAPER TAB */}
        <Tabs.Content value="paper">
          <Grid
            templateColumns={{ base: "1fr", md: "repeat(3, 1fr)" }}
            gap={6}
            mb={8}
          >
            <StatCard
              label="Simulated P&L"
              value={paperPnl?.realized_pnl}
              type="currency"
              isLoading={paperLoading}
            />
            <StatCard
              label="Paper Win Rate"
              value={paperPnl?.win_rate}
              type="percent"
              isLoading={paperLoading}
            />
            <StatCard
              label="Total Trades"
              value={paperPnl?.total_trades}
              type="number"
              isLoading={paperLoading}
            />
          </Grid>

          <Box
            p={8}
            textAlign="center"
            border="1px dashed"
            borderColor="gray.300"
            borderRadius="md"
          >
            <Text color="gray.500">
              Detailed Paper Trading logs are available in the "The Lab"
              workspace (Track B).
            </Text>
          </Box>
        </Tabs.Content>
      </Tabs.Root>
    </Container>
  )
}

function StatCard({
  label,
  value,
  type,
  isLoading,
}: {
  label: string
  value?: number
  type: "currency" | "percent" | "number"
  isLoading: boolean
}) {
  const format = (val: number | undefined) => {
    if (val === undefined) return "-"
    if (type === "currency") return `$${val.toFixed(2)}`
    if (type === "percent") return `${(val * 100).toFixed(1)}%`
    return val.toString()
  }

  return (
    <Card.Root variant="outline">
      <Card.Body>
        <Stat.Root>
          <Stat.Label color="gray.500">{label}</Stat.Label>
          {isLoading ? (
            <Text>...</Text>
          ) : (
            <Stat.ValueText
              fontWeight="bold"
              fontSize="2xl"
              color={
                type === "currency" && (value || 0) < 0
                  ? "red.500"
                  : type === "currency" && (value || 0) > 0
                    ? "green.500"
                    : "inherit"
              }
            >
              {format(value)}
            </Stat.ValueText>
          )}
        </Stat.Root>
      </Card.Body>
    </Card.Root>
  )
}
