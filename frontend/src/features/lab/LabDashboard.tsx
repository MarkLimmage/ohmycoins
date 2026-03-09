import {
  Box,
  Button,
  Flex,
  Heading,
  HStack,
  Text,
  VStack,
} from "@chakra-ui/react"
import { useState } from "react"
import { FiPlus } from "react-icons/fi"
import { OpenAPI } from "@/client"
import AgentTerminal from "@/components/Lab/AgentTerminal"
import { SessionCreateForm } from "./components/SessionCreateForm"
import { SessionList } from "./components/SessionList"
import { useCancelSession, useLabSessions } from "./hooks"
import { useLabWebSocket } from "./hooks/useLabWebSocket"

export function LabDashboard() {
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(
    null,
  )
  const [showCreateForm, setShowCreateForm] = useState(false)

  const { data: sessionsData } = useLabSessions()
  const cancelSession = useCancelSession()

  const { isDone } = useLabWebSocket({
    sessionId: selectedSessionId,
    enabled: !!selectedSessionId,
  })

  const selectedSession = sessionsData?.data?.find(
    (s) => s.id === selectedSessionId,
  )
  const isActive =
    selectedSession?.status === "pending" ||
    selectedSession?.status === "running"

  const baseUrl =
    OpenAPI.BASE?.replace(/^http/, "ws") || "wss://api.ohmycoins.com"
  const streamUrl = selectedSessionId
    ? `${baseUrl}/ws/agent/${selectedSessionId}/stream?token=${OpenAPI.TOKEN}`
    : ""

  const handleCancel = () => {
    if (selectedSessionId) {
      cancelSession.mutate(selectedSessionId)
    }
  }

  return (
    <VStack align="stretch" gap={6}>
      <HStack justify="space-between">
        <Heading size="lg">The Lab</Heading>
        <Button
          colorScheme="blue"
          size="sm"
          onClick={() => setShowCreateForm(true)}
        >
          <FiPlus />
          <Text ml={2}>New Session</Text>
        </Button>
      </HStack>

      <Text fontSize="sm" color="gray.500">
        Create AI agent sessions to analyze market data, train models, and
        generate trading strategies.
      </Text>

      <SessionCreateForm
        isOpen={showCreateForm}
        onClose={() => setShowCreateForm(false)}
        onCreated={(id) => {
          setSelectedSessionId(id)
          setShowCreateForm(false)
        }}
      />

      <Flex gap={6} direction={{ base: "column", lg: "row" }} minH="600px">
        {/* Left panel: Session list */}
        <Box w={{ base: "full", lg: "350px" }} flexShrink={0}>
          <SessionList
            sessions={sessionsData?.data || []}
            selectedId={selectedSessionId}
            onSelect={setSelectedSessionId}
          />
        </Box>

        {/* Right panel: Terminal */}
        <Box flex={1} minH="500px">
          {selectedSessionId ? (
            <AgentTerminal
              sessionId={selectedSessionId}
              streamUrl={streamUrl}
              allowInteraction={isActive && !isDone}
              onCancel={isActive ? handleCancel : undefined}
            />
          ) : (
            <Flex
              h="full"
              align="center"
              justify="center"
              bg="gray.900"
              borderRadius="lg"
              border="1px solid"
              borderColor="whiteAlpha.300"
            >
              <VStack gap={3} color="gray.500">
                <Text fontSize="lg">No session selected</Text>
                <Text fontSize="sm">
                  Select a session from the list or create a new one
                </Text>
              </VStack>
            </Flex>
          )}
        </Box>
      </Flex>
    </VStack>
  )
}
