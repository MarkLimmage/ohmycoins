import { Box, Text } from "@chakra-ui/react"
import { useId } from "react"
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"
import { useColorModeValue } from "../../ui/color-mode"
import type { GlassLedgerData } from "../types"

interface GlassTVLChartProps {
  data: GlassLedgerData
  onDrillDown?: (id: string) => void
}

const formatCurrency = (value: number) => {
  if (value >= 1e9) return `$${(value / 1e9).toFixed(1)}B`
  if (value >= 1e6) return `$${(value / 1e6).toFixed(1)}M`
  if (value >= 1e3) return `$${(value / 1e3).toFixed(1)}K`
  return `$${value}`
}

const CustomTooltip = ({ active, payload, label }: any) => {
  const tooltipBg = useColorModeValue("white", "gray.800")
  const tooltipBorder = useColorModeValue("gray.200", "gray.600")

  if (active && payload && payload.length) {
    return (
      <Box
        bg={tooltipBg}
        p={3}
        border="1px solid"
        borderColor={tooltipBorder}
        borderRadius="md"
        boxShadow="lg"
        zIndex={10}
      >
        <Text fontWeight="bold" mb={2} fontSize="sm">
          {label}
        </Text>
        {payload.map((entry: any, index: number) => (
          <Text
            key={index}
            color={entry.color}
            fontSize="xs"
            fontWeight="medium"
          >
            {entry.name}: {formatCurrency(entry.value)}
          </Text>
        ))}
      </Box>
    )
  }
  return null
}

export function GlassTVLChart({ data, onDrillDown }: GlassTVLChartProps) {
  const gridColor = useColorModeValue("#e5e7eb", "#4b5563")
  const gradientId = useId()

  if (!data?.historicalData || data.historicalData.length === 0) {
    return (
      <Box
        height="200px"
        display="flex"
        alignItems="center"
        justifyContent="center"
        bg="gray.50"
        borderRadius="md"
      >
        <Text color="gray.500">No Chart Data Available</Text>
      </Box>
    )
  }

  return (
    <Box
      height="220px"
      width="100%"
      mb={4}
      cursor={onDrillDown ? "pointer" : "default"}
      onClick={() => onDrillDown?.(data.id)}
      role="img"
      aria-label="Glass Ledger TVL and Fees Chart"
    >
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart
          data={data.historicalData}
          margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
        >
          <defs>
            <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.2} />
              <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid
            vertical={false}
            stroke={gridColor}
            strokeDasharray="3 3"
          />
          <XAxis
            dataKey="date"
            tickLine={false}
            axisLine={false}
            tick={{ fontSize: 10, fill: "#9ca3af" }}
            minTickGap={30}
          />
          <YAxis
            yAxisId="left"
            orientation="left"
            tickLine={false}
            axisLine={false}
            tickFormatter={formatCurrency}
            tick={{ fontSize: 10, fill: "#9ca3af" }}
            scale="auto"
            includeHidden
          />
          <YAxis
            yAxisId="right"
            orientation="right"
            tickLine={false}
            axisLine={false}
            tickFormatter={formatCurrency}
            tick={{ fontSize: 10, fill: "#9ca3af" }}
            scale="linear"
            includeHidden
          />
          <Tooltip content={<CustomTooltip />} />
          <Area
            yAxisId="left"
            type="monotone"
            dataKey="tvl"
            name="TVL"
            stroke="#3b82f6"
            strokeWidth={2}
            fillOpacity={1}
            fill={`url(#${gradientId})`}
            activeDot={{ r: 4, strokeWidth: 0 }}
          />
          <Line
            yAxisId="right"
            type="monotone"
            dataKey="fees"
            name="Fees"
            stroke="#10b981"
            strokeWidth={2}
            strokeDasharray="4 4"
            dot={false}
            activeDot={{ r: 4, strokeWidth: 0 }}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </Box>
  )
}
