import {
  Alert,
  Box,
  Heading,
  HStack,
  Icon,
  Spinner,
  Text,
  VStack,
} from "@chakra-ui/react"
import { FiAlertCircle } from "react-icons/fi"
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  XAxis,
  YAxis,
} from "recharts"
import { Tooltip } from "@/components/ui/tooltip"
import { Checkbox } from "../../components/ui/checkbox"
import { useAutoRefresh } from "../../context/AutoRefreshContext"
import {
  useCollectorVolume,
  useExchangeHealth,
} from "../../hooks/useCollectors"

const ExchangeHealthLight = () => {
  const { data: health, isLoading } = useExchangeHealth()
  if (isLoading || !health) return null
  const colorMap: Record<string, string> = {
    green: "green.400",
    amber: "yellow.400",
    red: "red.400",
    unknown: "gray.400",
  }
  return (
    <Tooltip content={health.details}>
      <HStack gap={2} cursor="pointer">
        <Box w={3} h={3} borderRadius="full" bg={colorMap[health.status]} />
        <Text fontSize="sm" color="gray.600">
          Exchange
        </Text>
      </HStack>
    </Tooltip>
  )
}

export const CollectorHealth = () => {
  const {
    data: volumeData,
    isLoading: volumeLoading,
    error: volumeError,
  } = useCollectorVolume("24h")
  const { isEnabled, toggle } = useAutoRefresh()

  return (
    <Box p={5}>
      <VStack gap={6} align="stretch">
        <HStack justify="space-between">
          <HStack gap={6} align="center">
            <Heading size="lg">Items Collected Volume (Last 24 Hours)</Heading>
            <ExchangeHealthLight />
          </HStack>
          <Checkbox checked={isEnabled} onCheckedChange={() => toggle()}>
            Auto Refresh (30s)
          </Checkbox>
        </HStack>

        {/* Volume Chart */}
        {volumeError && (
          <Alert.Root status="error">
            <Icon as={FiAlertCircle} mr={2} />
            Failed to load volume data
          </Alert.Root>
        )}
        {volumeLoading ? (
          <Spinner size="md" />
        ) : (
          <Box height="400px">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={volumeData || []}
                margin={{
                  top: 20,
                  right: 30,
                  left: 20,
                  bottom: 5,
                }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <RechartsTooltip />
                <Legend />
                <Bar dataKey="Glass" stackId="a" fill="#8884d8" />
                <Bar dataKey="Human" stackId="a" fill="#82ca9d" />
                <Bar dataKey="Catalyst" stackId="a" fill="#ffc658" />
              </BarChart>
            </ResponsiveContainer>
          </Box>
        )}
      </VStack>
    </Box>
  )
}
