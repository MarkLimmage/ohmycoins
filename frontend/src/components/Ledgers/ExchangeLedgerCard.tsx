import { Box, Text, Flex, Grid } from "@chakra-ui/react";
import { LedgerCard } from "./LedgerCard";
import { type LedgerCardProps, type ExchangeLedgerData } from "./types";

/**
 * ExchangeLedgerCard - Price list
 * Shows real-time price data and portfolio value
 * REQ-UX-001, REQ-UX-004
 */
export function ExchangeLedgerCard(props: LedgerCardProps) {
  const data = props.data as ExchangeLedgerData | undefined;

  return (
    <LedgerCard {...props}>
      {props.showTableView ? (
        <ExchangeTableView data={data} />
      ) : (
        <ExchangeChartView data={data} onDrillDown={props.onDrillDown} />
      )}
    </LedgerCard>
  );
}

function ExchangeChartView({
  data,
  onDrillDown,
}: {
  data?: ExchangeLedgerData;
  onDrillDown?: (id: string) => void;
}) {
  if (!data) return null;

  const formatCurrency = (value: number) => {
    if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
    if (value >= 1e3) return `$${(value / 1e3).toFixed(2)}K`;
    return `$${value.toFixed(2)}`;
  };

  const formatPercentage = (value: number) => {
    const sign = value >= 0 ? "+" : "";
    return `${sign}${value.toFixed(2)}%`;
  };

  return (
    <Box>
      {/* Portfolio value summary */}
      <Box
        padding="16px"
        backgroundColor="#faf5ff"
        borderRadius="4px"
        marginBottom="16px"
        textAlign="center"
      >
        <Text fontSize="12px" color="#6b7280" marginBottom="4px">
          Portfolio Value
        </Text>
        <Text fontSize="32px" fontWeight="700" color="#111827">
          {formatCurrency(data.portfolioValue)}
        </Text>
      </Box>

      {/* Top gainer and loser */}
      <Grid templateColumns="repeat(2, 1fr)" gap="12px" marginBottom="16px">
        <Box
          padding="12px"
          backgroundColor="#f0fdf4"
          borderRadius="4px"
          borderLeft="4px solid #22c55e"
        >
          <Text fontSize="12px" color="#6b7280" marginBottom="4px">
            Top Gainer
          </Text>
          <Text fontSize="18px" fontWeight="600" color="#111827">
            {data.topGainer.symbol}
          </Text>
          <Text fontSize="16px" fontWeight="500" color="#22c55e">
            {formatPercentage(data.topGainer.change)}
          </Text>
        </Box>

        <Box
          padding="12px"
          backgroundColor="#fef2f2"
          borderRadius="4px"
          borderLeft="4px solid #ef4444"
        >
          <Text fontSize="12px" color="#6b7280" marginBottom="4px">
            Top Loser
          </Text>
          <Text fontSize="18px" fontWeight="600" color="#111827">
            {data.topLoser.symbol}
          </Text>
          <Text fontSize="16px" fontWeight="500" color="#ef4444">
            {formatPercentage(data.topLoser.change)}
          </Text>
        </Box>
      </Grid>

      {/* Sparklines */}
      <Box
        role="region"
        aria-label="Price sparklines"
        tabIndex={0}
      >
        <Text fontSize="12px" color="#6b7280" marginBottom="12px" fontWeight="600">
          Asset Performance
        </Text>
        <Flex flexDirection="column" gap="12px">
          {data.sparklines.slice(0, 5).map((asset) => (
            <Box
              key={asset.symbol}
              padding="12px"
              backgroundColor="#f9fafb"
              borderRadius="4px"
              cursor={onDrillDown ? "pointer" : "default"}
              onClick={() => onDrillDown?.(data.id)}
              _hover={onDrillDown ? { backgroundColor: "#f3f4f6" } : {}}
              _focus={{ outline: "2px solid #8b5cf6", outlineOffset: "4px" }}
              tabIndex={0}
              role="article"
              aria-label={`${asset.symbol} at ${formatCurrency(asset.currentPrice)} with ${formatPercentage(asset.change24h)} change`}
              onKeyDown={(e) => {
                if ((e.key === "Enter" || e.key === " ") && onDrillDown) {
                  e.preventDefault();
                  onDrillDown(data.id);
                }
              }}
            >
              <Flex justifyContent="space-between" alignItems="center">
                <Flex alignItems="center" gap="12px" flex="1">
                  <Text fontSize="14px" fontWeight="600" color="#111827" minWidth="60px">
                    {asset.symbol}
                  </Text>
                  <Box flex="1" height="32px" position="relative">
                    {/* Simplified sparkline visualization */}
                    <svg
                      width="100%"
                      height="100%"
                      viewBox="0 0 100 32"
                      preserveAspectRatio="none"
                      aria-hidden="true"
                    >
                      <polyline
                        points={generateSparklinePoints(asset.prices)}
                        fill="none"
                        stroke={asset.change24h >= 0 ? "#22c55e" : "#ef4444"}
                        strokeWidth="2"
                      />
                    </svg>
                  </Box>
                </Flex>
                <Flex flexDirection="column" alignItems="flex-end" minWidth="100px">
                  <Text fontSize="14px" fontWeight="600" color="#111827">
                    {formatCurrency(asset.currentPrice)}
                  </Text>
                  <Text
                    fontSize="13px"
                    fontWeight="500"
                    color={asset.change24h >= 0 ? "#22c55e" : "#ef4444"}
                  >
                    {formatPercentage(asset.change24h)}
                  </Text>
                </Flex>
              </Flex>
            </Box>
          ))}
        </Flex>
      </Box>
    </Box>
  );
}

function ExchangeTableView({ data }: { data?: ExchangeLedgerData }) {
  if (!data) return null;

  return (
    <Box
      overflowX="auto"
      role="region"
      aria-label="Exchange price data table"
      tabIndex={0}
    >
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr style={{ borderBottom: "2px solid #e5e7eb" }}>
            <th style={{ padding: "12px", textAlign: "left", fontSize: "12px", fontWeight: 600, color: "#6b7280" }}>
              Asset
            </th>
            <th style={{ padding: "12px", textAlign: "right", fontSize: "12px", fontWeight: 600, color: "#6b7280" }}>
              Price
            </th>
            <th style={{ padding: "12px", textAlign: "right", fontSize: "12px", fontWeight: 600, color: "#6b7280" }}>
              24h Change
            </th>
          </tr>
        </thead>
        <tbody>
          <tr style={{ borderBottom: "1px solid #f3f4f6", backgroundColor: "#faf5ff" }}>
            <td colSpan={3} style={{ padding: "12px", fontSize: "14px", fontWeight: 600, textAlign: "center" }}>
              Portfolio Value: ${(data.portfolioValue / 1e3).toFixed(2)}K
            </td>
          </tr>
          {data.sparklines.slice(0, 10).map((asset) => (
            <tr key={asset.symbol} style={{ borderBottom: "1px solid #f3f4f6" }}>
              <td style={{ padding: "12px", fontSize: "14px", fontWeight: 500 }}>
                {asset.symbol}
              </td>
              <td style={{ padding: "12px", textAlign: "right", fontSize: "14px", fontWeight: 500 }}>
                ${asset.currentPrice.toFixed(2)}
              </td>
              <td style={{
                padding: "12px",
                textAlign: "right",
                fontSize: "14px",
                fontWeight: 500,
                color: asset.change24h >= 0 ? "#22c55e" : "#ef4444"
              }}>
                {asset.change24h >= 0 ? "+" : ""}{asset.change24h.toFixed(2)}%
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </Box>
  );
}

function generateSparklinePoints(prices: number[]): string {
  if (prices.length === 0) return "";

  const min = Math.min(...prices);
  const max = Math.max(...prices);
  const range = max - min || 1;

  return prices
    .map((price, index) => {
      const x = (index / (prices.length - 1)) * 100;
      const y = 32 - ((price - min) / range) * 32;
      return `${x},${y}`;
    })
    .join(" ");
}
