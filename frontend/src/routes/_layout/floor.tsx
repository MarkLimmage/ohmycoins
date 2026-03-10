import { Box, Container, Flex, Heading, Text } from "@chakra-ui/react"
import { createFileRoute } from "@tanstack/react-router"
import { useState } from "react"
import { BacktestConfigPanel } from "@/features/floor/components/BacktestConfigPanel"
import { BacktestResultsPanel } from "@/features/floor/components/BacktestResultsPanel"
import { FloorLayout } from "@/features/floor/components/FloorLayout"
import {
  useBacktestList,
  useBacktestResults,
} from "@/features/floor/hooks/useBacktest"

export const Route = createFileRoute("/_layout/floor")({
  component: FloorPage,
})

function FloorPage() {
  const [activeTab, setActiveTab] = useState<"algorithms" | "backtesting">(
    "algorithms",
  )
  const [selectedBacktestId, setSelectedBacktestId] = useState<string | null>(
    null,
  )
  const { data: backtestResult } = useBacktestResults(selectedBacktestId)
  const { data: backtestList } = useBacktestList()

  return (
    <Container maxW="full" py={4}>
      <Heading size="lg" mb={4}>
        The Floor
      </Heading>

      {/* Tab Navigation */}
      <Flex gap={4} mb={6} borderBottomWidth={1} pb={2}>
        <Text
          cursor="pointer"
          fontWeight={activeTab === "algorithms" ? "bold" : "normal"}
          color={activeTab === "algorithms" ? "blue.600" : "fg.muted"}
          borderBottomWidth={activeTab === "algorithms" ? 2 : 0}
          borderColor="blue.600"
          pb={1}
          onClick={() => setActiveTab("algorithms")}
        >
          Algorithms
        </Text>
        <Text
          cursor="pointer"
          fontWeight={activeTab === "backtesting" ? "bold" : "normal"}
          color={activeTab === "backtesting" ? "blue.600" : "fg.muted"}
          borderBottomWidth={activeTab === "backtesting" ? 2 : 0}
          borderColor="blue.600"
          pb={1}
          onClick={() => setActiveTab("backtesting")}
        >
          Backtesting
        </Text>
      </Flex>

      {activeTab === "algorithms" && <FloorLayout />}

      {activeTab === "backtesting" && (
        <Flex gap={6} direction={{ base: "column", lg: "row" }}>
          <Box flex={1}>
            <BacktestConfigPanel
              onBacktestCreated={(id) => setSelectedBacktestId(id)}
            />

            {/* Backtest History */}
            {backtestList?.data && backtestList.data.length > 0 && (
              <Box mt={4} p={4} borderWidth={1} borderRadius="lg">
                <Heading size="sm" mb={3}>
                  History
                </Heading>
                {backtestList.data.map((bt) => (
                  <Flex
                    key={bt.id}
                    p={2}
                    cursor="pointer"
                    borderRadius="md"
                    bg={
                      selectedBacktestId === bt.id ? "blue.50" : "transparent"
                    }
                    _hover={{ bg: "gray.50" }}
                    onClick={() => setSelectedBacktestId(bt.id)}
                    justify="space-between"
                    align="center"
                  >
                    <Text fontSize="sm">
                      {bt.coin_type} —{" "}
                      {new Date(bt.created_at).toLocaleDateString()}
                    </Text>
                    <Text
                      fontSize="xs"
                      color={
                        bt.status === "completed"
                          ? "green.600"
                          : bt.status === "failed"
                            ? "red.600"
                            : "orange.600"
                      }
                    >
                      {bt.status}
                    </Text>
                  </Flex>
                ))}
              </Box>
            )}
          </Box>

          <Box flex={2}>
            <BacktestResultsPanel backtest={backtestResult ?? null} />
          </Box>
        </Flex>
      )}
    </Container>
  )
}
