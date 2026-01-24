import { Box, Flex, Grid, Text } from "@chakra-ui/react"
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
      {/* Simplified sentiment heatmap placeholder */}
      <Box
        height="200px"
        backgroundColor="#f0fdf4"
        borderRadius="4px"
        display="flex"
        alignItems="center"
        justifyContent="center"
        flexDirection="column"
        marginBottom="16px"
        position="relative"
        role="img"
        aria-label={`Human Ledger showing ${getSentimentLabel(data.sentiment)} sentiment with score ${(data.sentimentScore * 100).toFixed(0)}`}
        tabIndex={0}
        _focus={{ outline: "2px solid #10b981", outlineOffset: "4px" }}
        cursor={onDrillDown ? "pointer" : "default"}
        onClick={() => onDrillDown?.(data.id)}
        _hover={onDrillDown ? { backgroundColor: "#dcfce7" } : {}}
      >
        <Text fontSize="64px" marginBottom="8px">
          {getSentimentEmoji(data.sentiment)}
        </Text>
        <Text
          fontSize="24px"
          fontWeight="600"
          color={getSentimentColor(data.sentiment)}
        >
          {getSentimentLabel(data.sentiment)}
        </Text>
        <Text fontSize="14px" color="#6b7280" marginTop="4px">
          Score: {(data.sentimentScore * 100).toFixed(0)}
        </Text>
      </Box>

      <Grid templateColumns="repeat(2, 1fr)" gap="12px">
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
