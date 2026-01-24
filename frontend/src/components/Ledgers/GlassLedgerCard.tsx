import { Box, Text, Flex, Grid } from "@chakra-ui/react";
import { LedgerCard } from "./LedgerCard";
import { type LedgerCardProps, type GlassLedgerData } from "./types";

/**
 * GlassLedgerCard - TVL and Fee display
 * Shows Total Value Locked and protocol fees
 * REQ-UX-001, REQ-UX-004
 */
export function GlassLedgerCard(props: LedgerCardProps) {
  const data = props.data as GlassLedgerData | undefined;

  return (
    <LedgerCard {...props}>
      {props.showTableView ? (
        <GlassTableView data={data} />
      ) : (
        <GlassChartView data={data} onDrillDown={props.onDrillDown} />
      )}
    </LedgerCard>
  );
}

function GlassChartView({
  data,
  onDrillDown,
}: {
  data?: GlassLedgerData;
  onDrillDown?: (id: string) => void;
}) {
  if (!data) return null;

  const formatCurrency = (value: number) => {
    if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
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
      {/* Simplified chart placeholder - no complex charts for MVP */}
      <Box
        height="200px"
        backgroundColor="#eff6ff"
        borderRadius="4px"
        display="flex"
        alignItems="center"
        justifyContent="center"
        marginBottom="16px"
        position="relative"
        role="img"
        aria-label={`Glass Ledger showing TVL of ${formatCurrency(data.tvl)} with ${formatPercentage(data.tvlChange24h)} change in 24 hours`}
        tabIndex={0}
        _focus={{ outline: "2px solid #3b82f6", outlineOffset: "4px" }}
        cursor={onDrillDown ? "pointer" : "default"}
        onClick={() => onDrillDown?.(data.id)}
        _hover={onDrillDown ? { backgroundColor: "#dbeafe" } : {}}
      >
        <Text fontSize="14px" color="#6b7280">
          Chart visualization
        </Text>
      </Box>

      <Grid templateColumns="repeat(3, 1fr)" gap="12px">
        <MetricCard
          label="Total Value Locked"
          value={formatCurrency(data.tvl)}
          change={data.tvlChange24h}
          color="#3b82f6"
        />
        <MetricCard
          label="Fees (24h)"
          value={formatCurrency(data.fees)}
          change={data.feesChange24h}
          color="#3b82f6"
        />
        <MetricCard
          label="Revenue"
          value={formatCurrency(data.revenue)}
          color="#3b82f6"
        />
      </Grid>
    </Box>
  );
}

function GlassTableView({ data }: { data?: GlassLedgerData }) {
  if (!data) return null;

  return (
    <Box
      overflowX="auto"
      role="region"
      aria-label="Glass Ledger data table"
      tabIndex={0}
    >
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr style={{ borderBottom: "2px solid #e5e7eb" }}>
            <th style={{ padding: "12px", textAlign: "left", fontSize: "12px", fontWeight: 600, color: "#6b7280" }}>
              Metric
            </th>
            <th style={{ padding: "12px", textAlign: "right", fontSize: "12px", fontWeight: 600, color: "#6b7280" }}>
              Value
            </th>
            <th style={{ padding: "12px", textAlign: "right", fontSize: "12px", fontWeight: 600, color: "#6b7280" }}>
              24h Change
            </th>
          </tr>
        </thead>
        <tbody>
          <tr style={{ borderBottom: "1px solid #f3f4f6" }}>
            <td style={{ padding: "12px", fontSize: "14px" }}>Total Value Locked</td>
            <td style={{ padding: "12px", textAlign: "right", fontSize: "14px", fontWeight: 500 }}>
              ${(data.tvl / 1e9).toFixed(2)}B
            </td>
            <td style={{ padding: "12px", textAlign: "right", fontSize: "14px", color: data.tvlChange24h >= 0 ? "#22c55e" : "#ef4444" }}>
              {data.tvlChange24h >= 0 ? "+" : ""}{data.tvlChange24h.toFixed(2)}%
            </td>
          </tr>
          <tr style={{ borderBottom: "1px solid #f3f4f6" }}>
            <td style={{ padding: "12px", fontSize: "14px" }}>Fees (24h)</td>
            <td style={{ padding: "12px", textAlign: "right", fontSize: "14px", fontWeight: 500 }}>
              ${(data.fees / 1e6).toFixed(2)}M
            </td>
            <td style={{ padding: "12px", textAlign: "right", fontSize: "14px", color: data.feesChange24h >= 0 ? "#22c55e" : "#ef4444" }}>
              {data.feesChange24h >= 0 ? "+" : ""}{data.feesChange24h.toFixed(2)}%
            </td>
          </tr>
          <tr>
            <td style={{ padding: "12px", fontSize: "14px" }}>Revenue</td>
            <td style={{ padding: "12px", textAlign: "right", fontSize: "14px", fontWeight: 500 }}>
              ${(data.revenue / 1e6).toFixed(2)}M
            </td>
            <td style={{ padding: "12px", textAlign: "right", fontSize: "14px" }}>-</td>
          </tr>
        </tbody>
      </table>
    </Box>
  );
}

function MetricCard({
  label,
  value,
  change,
  color,
}: {
  label: string;
  value: string;
  change?: number;
  color: string;
}) {
  return (
    <Box
      padding="12px"
      backgroundColor="#f9fafb"
      borderRadius="4px"
      borderLeft={`4px solid ${color}`}
    >
      <Text fontSize="12px" color="#6b7280" marginBottom="4px">
        {label}
      </Text>
      <Text fontSize="20px" fontWeight="600" color="#111827" marginBottom="4px">
        {value}
      </Text>
      {change !== undefined && (
        <Flex alignItems="center" gap="4px">
          <Text
            fontSize="14px"
            fontWeight="500"
            color={change >= 0 ? "#22c55e" : "#ef4444"}
          >
            {change >= 0 ? "↑" : "↓"} {Math.abs(change).toFixed(2)}%
          </Text>
          <Text fontSize="12px" color="#6b7280">
            24h
          </Text>
        </Flex>
      )}
    </Box>
  );
}
