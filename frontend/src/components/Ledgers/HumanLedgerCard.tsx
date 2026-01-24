import { Box, Flex, Grid, Text } from "@chakra-ui/react"
import { HumanSentimentHeatmap } from "./charts/HumanSentimentHeatmap"
import { LedgerCard } from "./LedgerCard"
import type { HumanLedgerData, LedgerCardProps } from "./types"

/**
 * HumanLedgerCard - Sentiment display
 * Shows social sentiment and trending topics
 * REQ-UX-001, REQ-UX-004
 */
export function HumanLedgerCard(props: LedgerCardProps) {
  const data = props.data as HumanLedgerData | undefined

  return (
    <LedgerCard {...props}>
      {props.showTableView ? (
        <HumanTableView data={data} />
      ) : (
        <HumanChartView data={data} onDrillDown={props.onDrillDown} />
      )}
    </LedgerCard>
  )
}

function HumanChartView({
  data,
  onDrillDown,
}: {
  data?: HumanLedgerData
  onDrillDown?: (id: string) => void
}) {
  if (!data) return null

  const getSentimentEmoji = (sentiment: string) => {
    switch (sentiment) {
      case "bullish":
        return "📈"
      case "bearish":
        return "📉"
      default:
        return "➡️"
    }
  }

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case "bullish":
        return "#22c55e"
      case "bearish":
        return "#ef4444"
      default:
        return "#6b7280"
    }
  }

  const getSentimentLabel = (sentiment: string) => {
    return sentiment.charAt(0).toUpperCase() + sentiment.slice(1)
  }

  return (
    <Box>
      <HumanSentimentHeatmap data={data} onDrillDown={onDrillDown} />

      <Grid templateColumns="repeat(3, 1fr)" gap="12px">
        <Box
          padding="12px"
          backgroundColor="#f0fdf4"
          borderRadius="4px"
          borderLeft="4px solid"
          borderLeftColor={getSentimentColor(data.sentiment)}
        >
          <Text fontSize="12px" color="#6b7280" marginBottom="4px">
            Current Sentiment
          </Text>
          <Flex alignItems="center" gap="8px">
            <Text fontSize="24px">{getSentimentEmoji(data.sentiment)}</Text>
            <Box>
              <Text fontSize="14px" fontWeight="600" color="#111827">
                {getSentimentLabel(data.sentiment)}
              </Text>
              <Text fontSize="12px" color="#6b7280">
                {/* Assuming data.sentimentScore exists in data */}
                Score: {data.sentimentScore?.toFixed(2)}
              </Text>
            </Box>
          </Flex>
        </Box>

        <Box
          padding="12px"
          backgroundColor="#f9fafb"
          borderRadius="4px"
          borderLeft="4px solid #10b981"
        >
          <Text fontSize="12px" color="#6b7280" marginBottom="8px">
            Trending Coins
          </Text>
          <Flex flexWrap="wrap" gap="4px">
            {data.trendingCoins.length > 0 ? (
              data.trendingCoins.slice(0, 5).map((coin) => (
                <Box
                  key={coin}
                  padding="4px 8px"
                  backgroundColor="#10b981"
                  color="white"
                  borderRadius="4px"
                  fontSize="12px"
                  fontWeight="500"
                >
                  {coin}
                </Box>
              ))
            ) : (
              <Text fontSize="12px" color="#6b7280">
                No trending coins
              </Text>
            )}
          </Flex>
        </Box>

        <Box
          padding="12px"
          backgroundColor="#f9fafb"
          borderRadius="4px"
          borderLeft="4px solid #10b981"
        >
          <Text fontSize="12px" color="#6b7280" marginBottom="4px">
            News Volume
          </Text>
          <Text fontSize="24px" fontWeight="600" color="#111827">
            {data.newsVolume.toLocaleString()}
          </Text>
          <Text fontSize="12px" color="#6b7280">
            articles today
          </Text>
        </Box>
      </Grid>
    </Box>
  )
}

function HumanTableView({ data }: { data?: HumanLedgerData }) {
  if (!data) return null

  return (
    <Box
      overflowX="auto"
      role="region"
      aria-label="Human Ledger data table"
      tabIndex={0}
    >
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr style={{ borderBottom: "2px solid #e5e7eb" }}>
            <th
              style={{
                padding: "12px",
                textAlign: "left",
                fontSize: "12px",
                fontWeight: 600,
                color: "#6b7280",
              }}
            >
              Metric
            </th>
            <th
              style={{
                padding: "12px",
                textAlign: "right",
                fontSize: "12px",
                fontWeight: 600,
                color: "#6b7280",
              }}
            >
              Value
            </th>
          </tr>
        </thead>
        <tbody>
          <tr style={{ borderBottom: "1px solid #f3f4f6" }}>
            <td style={{ padding: "12px", fontSize: "14px" }}>
              Overall Sentiment
            </td>
            <td
              style={{
                padding: "12px",
                textAlign: "right",
                fontSize: "14px",
                fontWeight: 500,
              }}
            >
              {data.sentiment.charAt(0).toUpperCase() + data.sentiment.slice(1)}
            </td>
          </tr>
          <tr style={{ borderBottom: "1px solid #f3f4f6" }}>
            <td style={{ padding: "12px", fontSize: "14px" }}>
              Sentiment Score
            </td>
            <td
              style={{
                padding: "12px",
                textAlign: "right",
                fontSize: "14px",
                fontWeight: 500,
              }}
            >
              {(data.sentimentScore * 100).toFixed(0)}
            </td>
          </tr>
          <tr style={{ borderBottom: "1px solid #f3f4f6" }}>
            <td style={{ padding: "12px", fontSize: "14px" }}>News Volume</td>
            <td
              style={{
                padding: "12px",
                textAlign: "right",
                fontSize: "14px",
                fontWeight: 500,
              }}
            >
              {data.newsVolume.toLocaleString()} articles
            </td>
          </tr>
          <tr>
            <td style={{ padding: "12px", fontSize: "14px" }}>
              Trending Coins
            </td>
            <td
              style={{
                padding: "12px",
                textAlign: "right",
                fontSize: "14px",
                fontWeight: 500,
              }}
            >
              {data.trendingCoins.length > 0
                ? data.trendingCoins.join(", ")
                : "None"}
            </td>
          </tr>
        </tbody>
      </table>
    </Box>
  )
}
