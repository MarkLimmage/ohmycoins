import { Box, Flex, Text } from "@chakra-ui/react"
import type { PLTickerData } from "../types"

interface PLTickerProps {
  data: PLTickerData
}

export const PLTicker = ({ data }: PLTickerProps) => {
  const isPositive = data.total_pnl >= 0
  const bgGradient = isPositive
    ? "linear-gradient(to right, #10b981, #059669)"
    : "linear-gradient(to right, #ef4444, #dc2626)"

  return (
    <Box
      w="full"
      h="60px"
      bg={bgGradient}
      color="white"
      px={4}
      aria-live="polite"
      role="status"
    >
      <Flex
        h="full"
        alignItems="center"
        justifyContent="space-between"
        fontSize="18px"
        fontWeight="bold"
      >
        <Flex gap={4}>
          <Text>
            P&L: {data.total_pnl >= 0 ? "+" : ""}${data.total_pnl.toFixed(2)} (
            {data.total_pnl >= 0 ? "+" : ""}
            {(data.pnl_percentage * 100).toFixed(1)}%)
          </Text>
          <Text>|</Text>
          <Text>Active: {data.active_count}</Text>
          <Text>|</Text>
          <Text>Paused: {data.paused_count}</Text>
        </Flex>

        <Flex alignItems="center" gap={2}>
          {data.is_connected ? (
            <>
              <Box w="3" h="3" borderRadius="full" bg="green.400" />
              <Text>LIVE</Text>
            </>
          ) : (
            <>
              <Box w="3" h="3" borderRadius="full" bg="red.400" />
              <Text>DISCONNECTED</Text>
            </>
          )}
        </Flex>
      </Flex>
    </Box>
  )
}
