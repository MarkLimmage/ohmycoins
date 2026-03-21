import { Box, Flex, Icon, Text, VStack } from "@chakra-ui/react"
import { useEffect, useRef } from "react"
import { FiAlertTriangle, FiMessageSquare, FiUser } from "react-icons/fi"
import { useLabContext } from "../context/LabContext"
import type { DialogueMessage, LabStage } from "../types"
import { ChatInput } from "./ChatInput"
import { ApprovalCard } from "./cards/ApprovalCard"
import { CircuitBreakerCard } from "./cards/CircuitBreakerCard"
import { ModelSelectionCard } from "./cards/ModelSelectionCard"
import { ScopeConfirmationCard } from "./cards/ScopeConfirmationCard"

const MessageBubble = ({ message }: { message: DialogueMessage }) => {
  const isUser = message.type === "user"
  const isError = message.type === "error"

  // G8: Differentiate senders
  const align = isUser ? "flex-end" : "flex-start"
  const bg = isUser ? "gray.100" : isError ? "red.50" : "blue.50"
  const color = isUser ? "gray.800" : isError ? "red.800" : "blue.900"
  const borderColor = isError ? "red.200" : !isUser ? "blue.200" : "transparent"
  const icon = isUser ? FiUser : isError ? FiAlertTriangle : FiMessageSquare
  const label = isUser ? "You" : isError ? "Error" : "Agent"

  // Error messages render full-width
  if (isError) {
    return (
      <Box
        w="100%"
        p={3}
        borderRadius="lg"
        bg="red.50"
        color="red.800"
        border="1px solid"
        borderColor="red.200"
        boxShadow="sm"
        mb={2}
      >
        <Flex align="center" mb={1} gap={2}>
          <Icon as={FiAlertTriangle} size="sm" color="red.500" />
          <Text fontSize="xs" fontWeight="bold" color="red.500">
            Error
          </Text>
        </Flex>
        <Text whiteSpace="pre-wrap" fontSize="sm">
          {message.content}
        </Text>
      </Box>
    )
  }

  return (
    <Flex w="100%" justify={align} mb={2}>
      <Box
        maxW="85%"
        p={3}
        borderRadius="lg"
        bg={bg}
        color={color}
        border="1px solid"
        borderColor={borderColor}
        boxShadow="sm"
      >
        <Flex align="center" mb={1} gap={2}>
          <Icon as={icon} size="sm" opacity={0.7} />
          <Text fontSize="xs" fontWeight="bold" opacity={0.7}>
            {label}
          </Text>
        </Flex>
        <Text whiteSpace="pre-wrap" fontSize="sm">
          {message.content}
        </Text>
      </Box>
    </Flex>
  )
}

/** Dispatch action_request messages to the appropriate inline HITL card */
const ActionRequestMessage = ({ message }: { message: DialogueMessage }) => {
  const actionId = message.actionPayload?.action_id || ""

  const commonProps = {
    messageId: message.id,
    payload: message.actionPayload || {},
    resolved: message.resolved,
    resolvedOption: message.resolvedOption,
  }

  switch (actionId) {
    case "scope_confirmation_v1":
      return <ScopeConfirmationCard {...commonProps} />
    case "approve_modeling_v1":
      return <ApprovalCard {...commonProps} />
    case "model_selection_v1":
      return <ModelSelectionCard {...commonProps} />
    case "circuit_breaker_v1":
      return <CircuitBreakerCard {...commonProps} />
    default:
      // Fallback: render as a generic action request card
      return <ApprovalCard {...commonProps} />
  }
}

export const DialoguePanel = ({ stage }: { stage?: LabStage }) => {
  const { state } = useLabContext()
  const { dialogueMessages, isConnected } = state
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Filter messages by stage when prop is provided
  const filteredMessages = stage
    ? dialogueMessages.filter((m) => m.stage === stage)
    : dialogueMessages

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [])

  return (
    <Flex
      direction="column"
      h="100%"
      bg="white"
      borderRight="1px solid"
      borderColor="gray.200"
    >
      {/* Header */}
      <Box p={3} borderBottom="1px solid" borderColor="gray.200" bg="gray.50">
        <Flex justify="space-between" align="center">
          <Text fontWeight="bold" fontSize="sm">
            Dialogue Stream
          </Text>
          <Flex align="center" gap={2}>
            <Box
              w={2}
              h={2}
              borderRadius="full"
              bg={isConnected ? "green.500" : "red.500"}
            />
            <Text fontSize="xs" color="gray.500">
              {isConnected ? "WS: LIVE" : "WS: DISCONNECTED"}
            </Text>
          </Flex>
        </Flex>
      </Box>

      {/* Messages Area */}
      <VStack
        flex={1}
        overflowY="auto"
        p={4}
        alignItems="stretch"
        gap={4}
        css={{
          "&::-webkit-scrollbar": { width: "4px" },
          "&::-webkit-scrollbar-track": { width: "6px" },
          "&::-webkit-scrollbar-thumb": {
            background: "#CBD5E0",
            borderRadius: "24px",
          },
        }}
      >
        {filteredMessages.map((msg) =>
          msg.type === "action_request" ? (
            <ActionRequestMessage key={msg.id} message={msg} />
          ) : msg.type === "divider" ? (
            <Box key={msg.id} textAlign="center" py={2}>
              <Text fontSize="xs" color="orange.500" fontWeight="bold">
                {msg.content}
              </Text>
            </Box>
          ) : (
            <MessageBubble key={msg.id} message={msg} />
          ),
        )}

        <div ref={messagesEndRef} />
      </VStack>

      {/* Input Area */}
      <ChatInput stage={stage} />
    </Flex>
  )
}
