import { Box, Button, Flex, Text } from "@chakra-ui/react"
import type { LedgerData, LedgerType } from "./types"

/**
 * LedgerTableView - Accessible table view for ledger data
 * Provides keyboard-navigable table alternative to charts
 * REQ-UX-001: Table view toggle for screen readers
 */
export interface LedgerTableViewProps {
  ledgerType: LedgerType
  data: LedgerData | undefined
  showTableView: boolean
  onToggleTableView: () => void
}

export function LedgerTableView({
  ledgerType,
  data,
  showTableView,
  onToggleTableView,
}: LedgerTableViewProps) {
  if (!data) {
    return (
      <Box
        textAlign="center"
        padding="32px"
        backgroundColor="#f9fafb"
        borderRadius="4px"
        role="status"
      >
        <Text fontSize="14px" color="#6b7280">
          No data available
        </Text>
      </Box>
    )
  }

  return (
    <Box>
      <Flex
        justifyContent="space-between"
        alignItems="center"
        marginBottom="16px"
      >
        <Text fontSize="16px" fontWeight="600" color="#111827">
          {showTableView ? "Table View" : "Chart View"}
        </Text>
        <Button
          size="sm"
          variant="outline"
          onClick={onToggleTableView}
          aria-label={`Switch to ${showTableView ? "chart" : "table"} view`}
          aria-pressed={showTableView}
          _focus={{ outline: "2px solid #3b82f6", outlineOffset: "4px" }}
        >
          {showTableView ? "View Chart" : "View Table"}
        </Button>
      </Flex>

      {showTableView && renderTableForLedgerType(ledgerType, data)}
    </Box>
  )
}

function renderTableForLedgerType(ledgerType: LedgerType, data: LedgerData) {
  switch (ledgerType) {
    case "glass":
      return <GlassTable data={data as any} />
    case "human":
      return <HumanTable data={data as any} />
    case "catalyst":
      return <CatalystTable data={data as any} />
    case "exchange":
      return <ExchangeTable data={data as any} />
    default:
      return null
  }
}

function GlassTable({ data }: { data: any }) {
  return (
    <Box
      overflowX="auto"
      role="region"
      aria-label="Glass Ledger data in table format"
      tabIndex={0}
    >
      <table
        style={{
          width: "100%",
          borderCollapse: "collapse",
          border: "1px solid #e5e7eb",
        }}
      >
        <thead>
          <tr style={{ backgroundColor: "#f9fafb" }}>
            <th
              style={{
                padding: "12px",
                textAlign: "left",
                fontSize: "14px",
                fontWeight: 600,
                color: "#111827",
                borderBottom: "2px solid #e5e7eb",
              }}
            >
              Metric
            </th>
            <th
              style={{
                padding: "12px",
                textAlign: "right",
                fontSize: "14px",
                fontWeight: 600,
                color: "#111827",
                borderBottom: "2px solid #e5e7eb",
              }}
            >
              Value
            </th>
            <th
              style={{
                padding: "12px",
                textAlign: "right",
                fontSize: "14px",
                fontWeight: 600,
                color: "#111827",
                borderBottom: "2px solid #e5e7eb",
              }}
            >
              24h Change
            </th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td
              style={{
                padding: "12px",
                fontSize: "14px",
                borderBottom: "1px solid #f3f4f6",
              }}
            >
              Total Value Locked
            </td>
            <td
              style={{
                padding: "12px",
                textAlign: "right",
                fontSize: "14px",
                fontWeight: 500,
                borderBottom: "1px solid #f3f4f6",
              }}
            >
              ${(data.tvl / 1e9).toFixed(2)}B
            </td>
            <td
              style={{
                padding: "12px",
                textAlign: "right",
                fontSize: "14px",
                fontWeight: 500,
                color: data.tvlChange24h >= 0 ? "#22c55e" : "#ef4444",
                borderBottom: "1px solid #f3f4f6",
              }}
            >
              {data.tvlChange24h >= 0 ? "+" : ""}
              {data.tvlChange24h.toFixed(2)}%
            </td>
          </tr>
          <tr>
            <td
              style={{
                padding: "12px",
                fontSize: "14px",
                borderBottom: "1px solid #f3f4f6",
              }}
            >
              Fees (24h)
            </td>
            <td
              style={{
                padding: "12px",
                textAlign: "right",
                fontSize: "14px",
                fontWeight: 500,
                borderBottom: "1px solid #f3f4f6",
              }}
            >
              ${(data.fees / 1e6).toFixed(2)}M
            </td>
            <td
              style={{
                padding: "12px",
                textAlign: "right",
                fontSize: "14px",
                fontWeight: 500,
                color: data.feesChange24h >= 0 ? "#22c55e" : "#ef4444",
                borderBottom: "1px solid #f3f4f6",
              }}
            >
              {data.feesChange24h >= 0 ? "+" : ""}
              {data.feesChange24h.toFixed(2)}%
            </td>
          </tr>
          <tr>
            <td style={{ padding: "12px", fontSize: "14px" }}>Revenue</td>
            <td
              style={{
                padding: "12px",
                textAlign: "right",
                fontSize: "14px",
                fontWeight: 500,
              }}
            >
              ${(data.revenue / 1e6).toFixed(2)}M
            </td>
            <td
              style={{ padding: "12px", textAlign: "right", fontSize: "14px" }}
            >
              -
            </td>
          </tr>
        </tbody>
      </table>
    </Box>
  )
}

function HumanTable({ data }: { data: any }) {
  return (
    <Box
      overflowX="auto"
      role="region"
      aria-label="Human Ledger data in table format"
      tabIndex={0}
    >
      <table
        style={{
          width: "100%",
          borderCollapse: "collapse",
          border: "1px solid #e5e7eb",
        }}
      >
        <thead>
          <tr style={{ backgroundColor: "#f9fafb" }}>
            <th
              style={{
                padding: "12px",
                textAlign: "left",
                fontSize: "14px",
                fontWeight: 600,
                color: "#111827",
                borderBottom: "2px solid #e5e7eb",
              }}
            >
              Metric
            </th>
            <th
              style={{
                padding: "12px",
                textAlign: "right",
                fontSize: "14px",
                fontWeight: 600,
                color: "#111827",
                borderBottom: "2px solid #e5e7eb",
              }}
            >
              Value
            </th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td
              style={{
                padding: "12px",
                fontSize: "14px",
                borderBottom: "1px solid #f3f4f6",
              }}
            >
              Overall Sentiment
            </td>
            <td
              style={{
                padding: "12px",
                textAlign: "right",
                fontSize: "14px",
                fontWeight: 500,
                borderBottom: "1px solid #f3f4f6",
              }}
            >
              {data.sentiment.charAt(0).toUpperCase() + data.sentiment.slice(1)}
            </td>
          </tr>
          <tr>
            <td
              style={{
                padding: "12px",
                fontSize: "14px",
                borderBottom: "1px solid #f3f4f6",
              }}
            >
              Sentiment Score
            </td>
            <td
              style={{
                padding: "12px",
                textAlign: "right",
                fontSize: "14px",
                fontWeight: 500,
                borderBottom: "1px solid #f3f4f6",
              }}
            >
              {(data.sentimentScore * 100).toFixed(0)}
            </td>
          </tr>
          <tr>
            <td
              style={{
                padding: "12px",
                fontSize: "14px",
                borderBottom: "1px solid #f3f4f6",
              }}
            >
              News Volume
            </td>
            <td
              style={{
                padding: "12px",
                textAlign: "right",
                fontSize: "14px",
                fontWeight: 500,
                borderBottom: "1px solid #f3f4f6",
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

function CatalystTable({ data }: { data: any }) {
  const formatDate = (date: Date) => {
    return new Intl.DateTimeFormat("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }).format(date)
  }

  return (
    <Box
      overflowX="auto"
      role="region"
      aria-label="Catalyst events in table format"
      tabIndex={0}
    >
      <table
        style={{
          width: "100%",
          borderCollapse: "collapse",
          border: "1px solid #e5e7eb",
        }}
      >
        <thead>
          <tr style={{ backgroundColor: "#f9fafb" }}>
            <th
              style={{
                padding: "12px",
                textAlign: "left",
                fontSize: "14px",
                fontWeight: 600,
                color: "#111827",
                borderBottom: "2px solid #e5e7eb",
              }}
            >
              Event
            </th>
            <th
              style={{
                padding: "12px",
                textAlign: "left",
                fontSize: "14px",
                fontWeight: 600,
                color: "#111827",
                borderBottom: "2px solid #e5e7eb",
              }}
            >
              Type
            </th>
            <th
              style={{
                padding: "12px",
                textAlign: "left",
                fontSize: "14px",
                fontWeight: 600,
                color: "#111827",
                borderBottom: "2px solid #e5e7eb",
              }}
            >
              Priority
            </th>
            <th
              style={{
                padding: "12px",
                textAlign: "right",
                fontSize: "14px",
                fontWeight: 600,
                color: "#111827",
                borderBottom: "2px solid #e5e7eb",
              }}
            >
              Time
            </th>
          </tr>
        </thead>
        <tbody>
          {data.events
            .slice(0, 10)
            .map((event: any, index: number, array: any[]) => (
              <tr key={event.id}>
                <td
                  style={{
                    padding: "12px",
                    fontSize: "14px",
                    fontWeight: 500,
                    borderBottom:
                      index === array.length - 1 ? "none" : "1px solid #f3f4f6",
                  }}
                >
                  {event.title}
                </td>
                <td
                  style={{
                    padding: "12px",
                    fontSize: "14px",
                    textTransform: "capitalize",
                    borderBottom:
                      index === array.length - 1 ? "none" : "1px solid #f3f4f6",
                  }}
                >
                  {event.type}
                </td>
                <td
                  style={{
                    padding: "12px",
                    fontSize: "14px",
                    fontWeight: 500,
                    textTransform: "uppercase",
                    color:
                      event.priority === "critical"
                        ? "#ef4444"
                        : event.priority === "high"
                          ? "#f59e0b"
                          : event.priority === "medium"
                            ? "#3b82f6"
                            : "#6b7280",
                    borderBottom:
                      index === array.length - 1 ? "none" : "1px solid #f3f4f6",
                  }}
                >
                  {event.priority}
                </td>
                <td
                  style={{
                    padding: "12px",
                    textAlign: "right",
                    fontSize: "13px",
                    color: "#6b7280",
                    borderBottom:
                      index === array.length - 1 ? "none" : "1px solid #f3f4f6",
                  }}
                >
                  {formatDate(event.timestamp)}
                </td>
              </tr>
            ))}
        </tbody>
      </table>
    </Box>
  )
}

function ExchangeTable({ data }: { data: any }) {
  return (
    <Box
      overflowX="auto"
      role="region"
      aria-label="Exchange price data in table format"
      tabIndex={0}
    >
      <table
        style={{
          width: "100%",
          borderCollapse: "collapse",
          border: "1px solid #e5e7eb",
        }}
      >
        <thead>
          <tr style={{ backgroundColor: "#f9fafb" }}>
            <th
              style={{
                padding: "12px",
                textAlign: "left",
                fontSize: "14px",
                fontWeight: 600,
                color: "#111827",
                borderBottom: "2px solid #e5e7eb",
              }}
            >
              Asset
            </th>
            <th
              style={{
                padding: "12px",
                textAlign: "right",
                fontSize: "14px",
                fontWeight: 600,
                color: "#111827",
                borderBottom: "2px solid #e5e7eb",
              }}
            >
              Price
            </th>
            <th
              style={{
                padding: "12px",
                textAlign: "right",
                fontSize: "14px",
                fontWeight: 600,
                color: "#111827",
                borderBottom: "2px solid #e5e7eb",
              }}
            >
              24h Change
            </th>
          </tr>
        </thead>
        <tbody>
          <tr style={{ backgroundColor: "#faf5ff" }}>
            <td
              colSpan={3}
              style={{
                padding: "12px",
                fontSize: "14px",
                fontWeight: 600,
                textAlign: "center",
                borderBottom: "2px solid #e5e7eb",
              }}
            >
              Portfolio Value: ${(data.portfolioValue / 1e3).toFixed(2)}K
            </td>
          </tr>
          {data.sparklines
            .slice(0, 10)
            .map((asset: any, index: number, array: any[]) => (
              <tr key={asset.symbol}>
                <td
                  style={{
                    padding: "12px",
                    fontSize: "14px",
                    fontWeight: 500,
                    borderBottom:
                      index === array.length - 1 ? "none" : "1px solid #f3f4f6",
                  }}
                >
                  {asset.symbol}
                </td>
                <td
                  style={{
                    padding: "12px",
                    textAlign: "right",
                    fontSize: "14px",
                    fontWeight: 500,
                    borderBottom:
                      index === array.length - 1 ? "none" : "1px solid #f3f4f6",
                  }}
                >
                  ${asset.currentPrice.toFixed(2)}
                </td>
                <td
                  style={{
                    padding: "12px",
                    textAlign: "right",
                    fontSize: "14px",
                    fontWeight: 500,
                    color: asset.change24h >= 0 ? "#22c55e" : "#ef4444",
                    borderBottom:
                      index === array.length - 1 ? "none" : "1px solid #f3f4f6",
                  }}
                >
                  {asset.change24h >= 0 ? "+" : ""}
                  {asset.change24h.toFixed(2)}%
                </td>
              </tr>
            ))}
        </tbody>
      </table>
    </Box>
  )
}
