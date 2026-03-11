import { Box, Text, VStack } from "@chakra-ui/react"
import {
  Bar,
  BarChart,
  Cell,
  ReferenceLine,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"
import { SafeChart } from "@/components/ui/safe-chart"

interface PredictionExplanationProps {
  shapValues: Record<string, number>
  baseValue: number
  prediction: number | string
}

export function PredictionExplanation({
  shapValues,
  baseValue,
  prediction,
}: PredictionExplanationProps) {
  const data = Object.entries(shapValues)
    .map(([name, value]) => ({ name, value: Number(value.toFixed(4)) }))
    .sort((a, b) => Math.abs(b.value) - Math.abs(a.value))

  return (
    <VStack align="stretch" gap={2}>
      <Text fontSize="xs" fontWeight="bold" color="gray.400">
        Prediction Explanation (SHAP)
      </Text>
      <Text fontSize="xs" color="gray.500">
        Base value: {baseValue.toFixed(4)} → Prediction: {String(prediction)}
      </Text>
      <Box h={`${Math.max(150, data.length * 28)}px`}>
        <SafeChart>
          <BarChart
            data={data}
            layout="vertical"
            margin={{ left: 100, right: 20, top: 5, bottom: 5 }}
          >
            <XAxis type="number" tick={{ fontSize: 10, fill: "#A0AEC0" }} />
            <YAxis
              type="category"
              dataKey="name"
              tick={{ fontSize: 10, fill: "#A0AEC0" }}
              width={95}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "#1A202C",
                border: "1px solid #4A5568",
                borderRadius: "4px",
                fontSize: "12px",
              }}
            />
            <ReferenceLine x={0} stroke="#718096" />
            <Bar dataKey="value" radius={[0, 4, 4, 0]}>
              {data.map((entry) => (
                <Cell
                  key={entry.name}
                  fill={entry.value >= 0 ? "#48BB78" : "#FC8181"}
                />
              ))}
            </Bar>
          </BarChart>
        </SafeChart>
      </Box>
    </VStack>
  )
}
