import { Box, HStack, Text, VStack } from "@chakra-ui/react"

export interface TrainingMetric {
  name: string
  value: number
  unit?: string
}

export interface FeatureImportanceItem {
  name: string
  importance: number
}

interface TrainingProgressChartProps {
  metrics: TrainingMetric[]
  featureImportance?: FeatureImportanceItem[]
}

export function TrainingProgressChart({
  metrics,
  featureImportance,
}: TrainingProgressChartProps) {
  return (
    <VStack
      align="stretch"
      gap={6}
      bg="gray.800"
      borderRadius="lg"
      p={4}
      border="1px solid"
      borderColor="gray.700"
    >
      {/* Metrics Table */}
      {metrics.length > 0 && (
        <VStack align="stretch" gap={2}>
          <Text fontSize="sm" fontWeight="bold" color="gray.300">
            Training Metrics
          </Text>
          <VStack align="stretch" gap={1}>
            {metrics.map((metric) => (
              <HStack key={metric.name} justify="space-between" fontSize="sm">
                <Text color="gray.400">{metric.name}</Text>
                <Text fontWeight="medium">
                  {typeof metric.value === "number"
                    ? metric.value.toFixed(4)
                    : metric.value}
                  {metric.unit ? ` ${metric.unit}` : ""}
                </Text>
              </HStack>
            ))}
          </VStack>
        </VStack>
      )}

      {/* Feature Importance Bars */}
      {featureImportance && featureImportance.length > 0 && (
        <VStack align="stretch" gap={2}>
          <Text fontSize="sm" fontWeight="bold" color="gray.300">
            Feature Importance
          </Text>
          <VStack align="stretch" gap={3}>
            {featureImportance.map((item) => {
              const percentage = Math.min(
                Math.max(item.importance * 100, 0),
                100,
              )
              return (
                <VStack key={item.name} align="stretch" gap={1}>
                  <HStack justify="space-between" fontSize="xs">
                    <Text color="gray.400">{item.name}</Text>
                    <Text fontWeight="medium" color="gray.300">
                      {percentage.toFixed(1)}%
                    </Text>
                  </HStack>
                  <Box
                    h="6px"
                    bg="gray.700"
                    borderRadius="sm"
                    overflow="hidden"
                  >
                    <Box
                      h="full"
                      bg="linear-gradient(90deg, #48bb78 0%, #38a169 100%)"
                      style={{ width: `${percentage}%` }}
                      transition="width 0.3s ease"
                    />
                  </Box>
                </VStack>
              )
            })}
          </VStack>
        </VStack>
      )}
    </VStack>
  )
}
