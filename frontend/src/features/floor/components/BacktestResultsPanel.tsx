import { Box, Flex, Heading, Spinner, Text } from "@chakra-ui/react"
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"
import type { BacktestRunPublic } from "@/client"

interface BacktestResultsPanelProps {
  backtest: BacktestRunPublic | null
  isLoading?: boolean
}

interface MetricDisplayProps {
  label: string
  value: string
  color?: string
}

const MetricDisplay = ({ label, value, color }: MetricDisplayProps) => (
  <Box p={2} borderWidth={1} borderRadius="md" textAlign="center">
    <Text fontSize="xs" color="fg.muted">
      {label}
    </Text>
    <Text fontSize="md" fontWeight="bold" color={color}>
      {value}
    </Text>
  </Box>
)

export const BacktestResultsPanel = ({
  backtest,
  isLoading,
}: BacktestResultsPanelProps) => {
  if (isLoading) {
    return (
      <Flex justify="center" align="center" p={8}>
        <Spinner size="lg" />
        <Text ml={3}>Running backtest...</Text>
      </Flex>
    )
  }

  if (!backtest) return null

  if (backtest.status === "failed") {
    return (
      <Box p={4} borderWidth={1} borderRadius="lg" bg="red.50">
        <Heading size="sm" color="red.600" mb={2}>
          Backtest Failed
        </Heading>
        <Text fontSize="sm">{backtest.error_message || "Unknown error"}</Text>
      </Box>
    )
  }

  if (backtest.status === "pending" || backtest.status === "running") {
    return (
      <Flex justify="center" align="center" p={8}>
        <Spinner size="lg" />
        <Text ml={3}>Backtest {backtest.status}...</Text>
      </Flex>
    )
  }

  // Parse results
  const metrics = backtest.results_json
    ? JSON.parse(backtest.results_json)
    : null
  const equityCurve = backtest.equity_curve_json
    ? JSON.parse(backtest.equity_curve_json)
    : []

  // Format equity curve for chart (sample if too many points)
  const maxPoints = 200
  const step = Math.max(1, Math.floor(equityCurve.length / maxPoints))
  const chartData = equityCurve
    .filter((_: unknown, i: number) => i % step === 0)
    .map((point: { timestamp: string; equity: number }) => ({
      timestamp: new Date(point.timestamp).toLocaleDateString(),
      equity: Math.round(point.equity * 100) / 100,
    }))

  return (
    <Box p={4} borderWidth={1} borderRadius="lg" bg="bg.surface">
      <Heading size="sm" mb={4}>
        Results — {backtest.coin_type}
      </Heading>

      {/* Metrics Grid */}
      {metrics && (
        <Flex wrap="wrap" gap={2} mb={4}>
          <MetricDisplay
            label="Total Return"
            value={`${(metrics.total_return * 100).toFixed(2)}%`}
            color={metrics.total_return >= 0 ? "green.600" : "red.600"}
          />
          <MetricDisplay
            label="Sharpe Ratio"
            value={metrics.sharpe_ratio.toFixed(2)}
          />
          <MetricDisplay
            label="Sortino Ratio"
            value={metrics.sortino_ratio.toFixed(2)}
          />
          <MetricDisplay
            label="Max Drawdown"
            value={`${(metrics.max_drawdown * 100).toFixed(2)}%`}
            color="red.600"
          />
          <MetricDisplay
            label="Win Rate"
            value={`${(metrics.win_rate * 100).toFixed(1)}%`}
          />
          <MetricDisplay
            label="Profit Factor"
            value={metrics.profit_factor.toFixed(2)}
          />
          <MetricDisplay label="Trades" value={String(metrics.num_trades)} />
        </Flex>
      )}

      {/* Equity Curve Chart */}
      {chartData.length > 0 && (
        <Box h="300px">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="timestamp" fontSize={10} />
              <YAxis fontSize={10} />
              <Tooltip />
              <Line
                type="monotone"
                dataKey="equity"
                stroke="#3182ce"
                dot={false}
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>
        </Box>
      )}
    </Box>
  )
}
