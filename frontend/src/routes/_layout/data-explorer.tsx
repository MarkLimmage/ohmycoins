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
import {
  transformPriceDataForBarChart,
  transformPriceDataForLineChart,
  usePriceData,
} from "../../hooks/useDataExplorer"

export const Route = createFileRoute("/_layout/data-explorer")({
  component: DataExplorerPage,
})

interface FilterState {
  coin: string
  ledger: "all" | "Glass" | "Human" | "Catalyst" | "Exchange"
  startDate: string
  endDate: string
}

function DataExplorerPage() {
  const [filters, setFilters] = useState<FilterState>({
    coin: "BTC",
    ledger: "all",
    startDate: "2026-02-26",
    endDate: "2026-02-27",
  })

  // Fetch price data for selected coin and date range
  const { data: priceDataResponse, isLoading: isPriceLoading } = usePriceData(
    filters.coin,
    filters.startDate,
    filters.endDate,
  )

  // Transform price data for charts
  const lineChartData = priceDataResponse?.data
    ? transformPriceDataForLineChart(priceDataResponse.data)
    : []

  const barChartData = priceDataResponse?.data
    ? transformPriceDataForBarChart(priceDataResponse.data)
    : []

  const isLoading = isPriceLoading

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
              ) : lineChartData.length === 0 ? (
                <Flex justify="center" align="center" py={8}>
                  <Text color="gray.500">
                    No price data available for the selected date range
                  </Text>
                </Flex>
              ) : (
                <Box height="400px" width="100%">
                  <ResponsiveContainer width="100%" height="100%" minWidth={0}>
                    <LineChart
                      data={lineChartData}
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
              ) : barChartData.length === 0 ? (
                <Flex justify="center" align="center" py={8}>
                  <Text color="gray.500">
                    No price data available for the selected date range
                  </Text>
                </Flex>
              ) : (
                <Box height="350px" width="100%">
                  <ResponsiveContainer width="100%" height="100%" minWidth={0}>
                    <BarChart
                      data={barChartData}
                      margin={{
                        top: 20,
                        right: 30,
                        left: 20,
                        bottom: 5,
                      }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="coin" />
                      <YAxis />
                      <RechartsTooltip />
                      <Legend />
                      <Bar dataKey="price" fill="#8884d8" name="Price (USD)" />
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
