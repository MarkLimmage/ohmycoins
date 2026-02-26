import {
  Box,
  Button,
  Card,
  Container,
  Flex,
  Heading,
  HStack,
  Spinner,
  Text,
  VStack,
} from "@chakra-ui/react"
import { createFileRoute } from "@tanstack/react-router"
import { useState } from "react"
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  XAxis,
  YAxis,
} from "recharts"

export const Route = createFileRoute("/_layout/data-explorer")({
  component: DataExplorerPage,
})

interface FilterState {
  coin: string
  ledger: "all" | "Glass" | "Human" | "Catalyst" | "Exchange"
  startDate: string
  endDate: string
}

const MOCK_PRICE_DATA = [
  {
    time: "2026-02-27 00:00",
    BTC: 45230,
    ETH: 2850,
    DOGE: 0.385,
    ADA: 1.12,
  },
  {
    time: "2026-02-27 04:00",
    BTC: 45450,
    ETH: 2875,
    DOGE: 0.388,
    ADA: 1.14,
  },
  {
    time: "2026-02-27 08:00",
    BTC: 45100,
    ETH: 2825,
    DOGE: 0.382,
    ADA: 1.11,
  },
  {
    time: "2026-02-27 12:00",
    BTC: 45800,
    ETH: 2900,
    DOGE: 0.391,
    ADA: 1.15,
  },
  {
    time: "2026-02-27 16:00",
    BTC: 45600,
    ETH: 2880,
    DOGE: 0.389,
    ADA: 1.13,
  },
]

function DataExplorerPage() {
  const [filters, setFilters] = useState<FilterState>({
    coin: "BTC",
    ledger: "all",
    startDate: "2026-02-26",
    endDate: "2026-02-27",
  })
  const [isLoading] = useState(false)

  const handleFilterChange = (key: keyof FilterState, value: string) => {
    setFilters((prev) => ({
      ...prev,
      [key]: value,
    }))
  }

  const handleSelectChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const { name, value } = e.target
    handleFilterChange(name as keyof FilterState, value)
  }

  const selectStyles = {
    width: "100%",
    padding: "8px",
    borderRadius: "4px",
    border: "1px solid #e2e8f0",
    fontSize: "14px",
  }

  return (
    <Container maxW="full" py={8}>
      <VStack gap={8} align="stretch">
        {/* Header */}
        <Box>
          <Heading size="lg" mb={2}>
            Data Explorer
          </Heading>
          <Text color="gray.500">
            Explore historical price data and collector metrics
          </Text>
        </Box>

        {/* Filter Controls Card */}
        <Card.Root variant="outline">
          <Card.Body>
            <VStack gap={6} align="stretch">
              <Heading size="md">Filters</Heading>

              <Flex gap={4} wrap={{ base: "wrap", md: "nowrap" }}>
                {/* Coin Selector */}
                <Box flex={1} minW="200px">
                  <Text fontSize="sm" fontWeight="medium" mb={2}>
                    Coin
                  </Text>
                  <select
                    name="coin"
                    value={filters.coin}
                    onChange={handleSelectChange}
                    style={selectStyles}
                  >
                    <option value="BTC">Bitcoin (BTC)</option>
                    <option value="ETH">Ethereum (ETH)</option>
                    <option value="DOGE">Dogecoin (DOGE)</option>
                    <option value="ADA">Cardano (ADA)</option>
                  </select>
                </Box>

                {/* Ledger Selector */}
                <Box flex={1} minW="200px">
                  <Text fontSize="sm" fontWeight="medium" mb={2}>
                    Data Source
                  </Text>
                  <select
                    name="ledger"
                    value={filters.ledger}
                    onChange={handleSelectChange}
                    style={selectStyles}
                  >
                    <option value="all">All Ledgers</option>
                    <option value="Glass">Glass (On-chain)</option>
                    <option value="Human">Human (News/Sentiment)</option>
                    <option value="Catalyst">Catalyst (Events)</option>
                    <option value="Exchange">Exchange (CoinSpot)</option>
                  </select>
                </Box>

                {/* Start Date */}
                <Box flex={1} minW="200px">
                  <Text fontSize="sm" fontWeight="medium" mb={2}>
                    Start Date
                  </Text>
                  <input
                    type="date"
                    name="startDate"
                    value={filters.startDate}
                    onChange={(e) =>
                      handleFilterChange("startDate", e.target.value)
                    }
                    style={selectStyles}
                  />
                </Box>

                {/* End Date */}
                <Box flex={1} minW="200px">
                  <Text fontSize="sm" fontWeight="medium" mb={2}>
                    End Date
                  </Text>
                  <input
                    type="date"
                    name="endDate"
                    value={filters.endDate}
                    onChange={(e) =>
                      handleFilterChange("endDate", e.target.value)
                    }
                    style={selectStyles}
                  />
                </Box>
              </Flex>

              <HStack justify="flex-end" gap={2}>
                <Button variant="outline">Reset Filters</Button>
                <Button colorScheme="blue">Apply</Button>
              </HStack>
            </VStack>
          </Card.Body>
        </Card.Root>

        {/* Chart Area */}
        <Card.Root variant="outline">
          <Card.Body>
            <VStack gap={6} align="stretch">
              <Heading size="md">
                Price Data: {filters.coin} ({filters.startDate} to{" "}
                {filters.endDate})
              </Heading>

              {isLoading ? (
                <Flex justify="center" py={8}>
                  <Spinner size="lg" />
                </Flex>
              ) : (
                <Box height="400px" width="100%">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart
                      data={MOCK_PRICE_DATA}
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
                      <RechartsTooltip />
                      <Legend />
                      <Line
                        type="monotone"
                        dataKey={filters.coin}
                        stroke="#8884d8"
                        dot={false}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </Box>
              )}
            </VStack>
          </Card.Body>
        </Card.Root>

        {/* Multi-Coin Comparison Chart */}
        <Card.Root variant="outline">
          <Card.Body>
            <VStack gap={6} align="stretch">
              <Heading size="md">All Coins Comparison (Last 24h)</Heading>

              {isLoading ? (
                <Flex justify="center" py={8}>
                  <Spinner size="lg" />
                </Flex>
              ) : (
                <Box height="350px" width="100%">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={MOCK_PRICE_DATA}
                      margin={{
                        top: 20,
                        right: 30,
                        left: 20,
                        bottom: 5,
                      }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="time" />
                      <YAxis yAxisId="left" />
                      <YAxis yAxisId="right" orientation="right" />
                      <RechartsTooltip />
                      <Legend />
                      <Bar
                        yAxisId="left"
                        dataKey="BTC"
                        fill="#f7931a"
                        name="BTC"
                      />
                      <Bar
                        yAxisId="left"
                        dataKey="ETH"
                        fill="#627eea"
                        name="ETH"
                      />
                      <Bar
                        yAxisId="right"
                        dataKey="DOGE"
                        fill="#c2a633"
                        name="DOGE"
                      />
                      <Bar
                        yAxisId="right"
                        dataKey="ADA"
                        fill="#0033ad"
                        name="ADA"
                      />
                    </BarChart>
                  </ResponsiveContainer>
                </Box>
              )}

              <Text fontSize="xs" color="gray.500">
                Note: Chart uses different Y-axes to accommodate price
                differences across coins
              </Text>
            </VStack>
          </Card.Body>
        </Card.Root>
      </VStack>
    </Container>
  )
}
