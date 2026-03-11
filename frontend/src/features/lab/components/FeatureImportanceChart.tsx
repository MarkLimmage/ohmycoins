import { Box, Text, VStack } from "@chakra-ui/react"
import { Bar, BarChart, Tooltip, XAxis, YAxis } from "recharts"
import { SafeChart } from "@/components/ui/safe-chart"

interface FeatureImportanceChartProps {
  features: { feature_name: string; importance: number }[]
}

export function FeatureImportanceChart({
  features,
}: FeatureImportanceChartProps) {
  const sorted = [...features].sort((a, b) => b.importance - a.importance)
  const data = sorted.map((f) => ({
    name: f.feature_name,
    importance: Number(f.importance.toFixed(4)),
  }))

  return (
    <VStack align="stretch" gap={2}>
      <Text fontSize="xs" fontWeight="bold" color="gray.400">
        Feature Importance (SHAP)
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
            <Bar dataKey="importance" fill="#4299E1" radius={[0, 4, 4, 0]} />
          </BarChart>
        </SafeChart>
      </Box>
    </VStack>
  )
}
