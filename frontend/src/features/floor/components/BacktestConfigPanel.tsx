import { Box, Button, Flex, Heading, Input, Text } from "@chakra-ui/react"
import { useState } from "react"
import { useRunBacktest } from "../hooks/useBacktest"

interface BacktestConfigPanelProps {
  onBacktestCreated?: (id: string) => void
}

export const BacktestConfigPanel = ({
  onBacktestCreated,
}: BacktestConfigPanelProps) => {
  const runBacktest = useRunBacktest()
  const [algorithmId, setAlgorithmId] = useState("")
  const [coinType, setCoinType] = useState("BTC")
  const [startDate, setStartDate] = useState("")
  const [endDate, setEndDate] = useState("")
  const [initialCapital, setInitialCapital] = useState("10000")

  const handleSubmit = async () => {
    if (!algorithmId || !startDate || !endDate) return

    try {
      const result = await runBacktest.mutateAsync({
        algorithm_id: algorithmId,
        coin_type: coinType,
        start_date: new Date(startDate).toISOString(),
        end_date: new Date(endDate).toISOString(),
        initial_capital: Number(initialCapital),
      })
      onBacktestCreated?.(result.id)
    } catch {
      // Error handled by mutation state
    }
  }

  return (
    <Box p={4} borderWidth={1} borderRadius="lg" bg="bg.surface">
      <Heading size="sm" mb={4}>
        Run Backtest
      </Heading>
      <Flex direction="column" gap={3}>
        <Box>
          <Text fontSize="sm" mb={1} fontWeight="medium">
            Algorithm ID
          </Text>
          <Input
            placeholder="Enter algorithm UUID"
            value={algorithmId}
            onChange={(e) => setAlgorithmId(e.target.value)}
            size="sm"
          />
        </Box>
        <Box>
          <Text fontSize="sm" mb={1} fontWeight="medium">
            Coin
          </Text>
          <Input
            placeholder="BTC"
            value={coinType}
            onChange={(e) => setCoinType(e.target.value)}
            size="sm"
          />
        </Box>
        <Flex gap={3}>
          <Box flex={1}>
            <Text fontSize="sm" mb={1} fontWeight="medium">
              Start Date
            </Text>
            <Input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              size="sm"
            />
          </Box>
          <Box flex={1}>
            <Text fontSize="sm" mb={1} fontWeight="medium">
              End Date
            </Text>
            <Input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              size="sm"
            />
          </Box>
        </Flex>
        <Box>
          <Text fontSize="sm" mb={1} fontWeight="medium">
            Initial Capital (AUD)
          </Text>
          <Input
            type="number"
            value={initialCapital}
            onChange={(e) => setInitialCapital(e.target.value)}
            size="sm"
          />
        </Box>
        <Button
          colorScheme="blue"
          onClick={handleSubmit}
          disabled={
            !algorithmId || !startDate || !endDate || runBacktest.isPending
          }
          size="sm"
        >
          {runBacktest.isPending ? "Running..." : "Run Backtest"}
        </Button>
        {runBacktest.isError && (
          <Text color="red.500" fontSize="sm">
            Backtest failed. Please check your inputs.
          </Text>
        )}
      </Flex>
    </Box>
  )
}
