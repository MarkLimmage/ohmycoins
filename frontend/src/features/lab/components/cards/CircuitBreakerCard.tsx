import {
  Box,
  Button,
  Flex,
  Heading,
  HStack,
  Icon,
  Text,
  VStack,
} from "@chakra-ui/react"
import type React from "react"
import { useState } from "react"
import { FiAlertOctagon, FiMessageCircle, FiXCircle } from "react-icons/fi"
import { AgentService } from "../../../../client"
import { useLabContext } from "../../context/LabContext"
import type { LabEventPayload } from "../../types"

interface CircuitBreakerCardProps {
  messageId: string
  payload: LabEventPayload
  resolved?: boolean
  resolvedOption?: string
}

export const CircuitBreakerCard: React.FC<CircuitBreakerCardProps> = ({
  messageId,
  payload,
  resolved,
  resolvedOption,
}) => {
  const { state, dispatch } = useLabContext()
  const [isSubmitting, setIsSubmitting] = useState(false)

  const suggestions: string[] = payload.suggestions || []

  const handleAction = async (option: string, suggestion?: string) => {
    if (!state.sessionId) return
    setIsSubmitting(true)
    try {
      if (option === "ABORT_SESSION") {
        await AgentService.approveRequest({
          sessionId: state.sessionId,
          requestBody: { approved: false, reason: "ABORT" },
        })
      } else if (option === "CHOOSE_SUGGESTION" && suggestion) {
        await AgentService.provideClarifications({
          sessionId: state.sessionId,
          requestBody: { responses: { suggestion } },
        })
      } else {
        // PROVIDE_GUIDANCE — user will type in ChatInput
        await AgentService.approveRequest({
          sessionId: state.sessionId,
          requestBody: { approved: true, reason: "USER_GUIDANCE" },
        })
      }
      dispatch({
        type: "RESOLVE_ACTION",
        payload: { messageId, option: suggestion || option },
      })
    } catch (error) {
      console.error("Failed to handle circuit breaker:", error)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Box
      w="100%"
      p={4}
      bg={resolved ? "gray.50" : "red.50"}
      borderLeft="4px solid"
      borderColor={resolved ? "gray.300" : "red.400"}
      borderRadius="md"
      boxShadow="sm"
      opacity={resolved ? 0.7 : 1}
    >
      <VStack align="stretch" gap={3}>
        <Flex align="center" gap={2}>
          <Icon as={FiAlertOctagon} color={resolved ? "gray.500" : "red.500"} />
          <Heading size="sm" color={resolved ? "gray.600" : "red.700"}>
            Circuit Breaker — Help Needed
          </Heading>
        </Flex>

        <Text fontSize="sm">{payload.description}</Text>

        {payload.last_error && (
          <Box
            bg="white"
            p={3}
            borderRadius="md"
            border="1px solid"
            borderColor="red.200"
          >
            <Text fontSize="xs" fontFamily="mono" color="red.600">
              {payload.last_error}
            </Text>
            {payload.attempts && (
              <Text fontSize="xs" color="gray.500" mt={1}>
                Stage: {payload.stage} · Attempts: {payload.attempts}
              </Text>
            )}
          </Box>
        )}

        {/* Suggestions as action buttons */}
        {resolved ? (
          <Text fontSize="xs" color="gray.500" fontStyle="italic">
            ✓ {resolvedOption}
          </Text>
        ) : (
          <VStack align="stretch" gap={2}>
            {suggestions.map((suggestion, i) => (
              <Button
                key={i}
                size="sm"
                variant="outline"
                colorScheme="blue"
                justifyContent="flex-start"
                onClick={() => handleAction("CHOOSE_SUGGESTION", suggestion)}
                loading={isSubmitting}
              >
                {suggestion}
              </Button>
            ))}
            <HStack gap={3} pt={1}>
              <Button
                size="sm"
                colorScheme="gray"
                variant="outline"
                onClick={() => handleAction("PROVIDE_GUIDANCE")}
                loading={isSubmitting}
              >
                <Icon as={FiMessageCircle} mr={1} />
                I'll type guidance
              </Button>
              <Button
                size="sm"
                colorScheme="red"
                variant="outline"
                onClick={() => handleAction("ABORT_SESSION")}
                loading={isSubmitting}
              >
                <Icon as={FiXCircle} mr={1} />
                Abort Session
              </Button>
            </HStack>
          </VStack>
        )}
      </VStack>
    </Box>
  )
}
