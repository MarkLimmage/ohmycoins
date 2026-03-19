import {
  Box,
  Button,
  Flex,
  Heading,
  HStack,
  Icon,
  Table,
  Text,
  VStack,
} from "@chakra-ui/react"
import type React from "react"
import { useState } from "react"
import { FiCheck, FiEdit, FiTarget } from "react-icons/fi"
import { AgentService } from "../../../../client"
import { useLabContext } from "../../context/LabContext"
import type { LabEventPayload } from "../../types"

interface ScopeConfirmationCardProps {
  messageId: string
  payload: LabEventPayload
  resolved?: boolean
  resolvedOption?: string
}

export const ScopeConfirmationCard: React.FC<ScopeConfirmationCardProps> = ({
  messageId,
  payload,
  resolved,
  resolvedOption,
}) => {
  const { state, dispatch } = useLabContext()
  const [isSubmitting, setIsSubmitting] = useState(false)
  const interpretation = payload.interpretation || {}

  const handleAction = async (option: string) => {
    if (!state.sessionId) return
    setIsSubmitting(true)
    try {
      if (option === "CONFIRM_SCOPE") {
        await AgentService.approveRequest({
          sessionId: state.sessionId,
          requestBody: { approved: true },
        })
      } else {
        await AgentService.provideClarifications({
          sessionId: state.sessionId,
          requestBody: { responses: {} },
        })
      }
      dispatch({
        type: "RESOLVE_ACTION",
        payload: { messageId, option },
      })
    } catch (error) {
      console.error("Failed to submit scope confirmation:", error)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Box
      w="100%"
      p={4}
      bg={resolved ? "gray.50" : "orange.50"}
      borderLeft="4px solid"
      borderColor={resolved ? "gray.300" : "orange.400"}
      borderRadius="md"
      boxShadow="sm"
      opacity={resolved ? 0.7 : 1}
    >
      <VStack align="stretch" gap={3}>
        <Flex align="center" gap={2}>
          <Icon as={FiTarget} color={resolved ? "gray.500" : "orange.500"} />
          <Heading size="sm" color={resolved ? "gray.600" : "orange.700"}>
            Scope Confirmation
          </Heading>
        </Flex>

        <Text fontSize="sm">{payload.description}</Text>

        {/* Interpretation Table */}
        {Object.keys(interpretation).length > 0 && (
          <Box
            borderRadius="md"
            overflow="hidden"
            border="1px solid"
            borderColor="gray.200"
          >
            <Table.Root size="sm">
              <Table.Body>
                {Object.entries(interpretation).map(([key, value]) => (
                  <Table.Row key={key}>
                    <Table.Cell
                      fontWeight="bold"
                      textTransform="capitalize"
                      bg="gray.50"
                      w="140px"
                    >
                      {key.replace(/_/g, " ")}
                    </Table.Cell>
                    <Table.Cell>
                      {Array.isArray(value) ? value.join(", ") : String(value)}
                    </Table.Cell>
                  </Table.Row>
                ))}
              </Table.Body>
            </Table.Root>
          </Box>
        )}

        {/* Questions */}
        {payload.questions?.length > 0 && (
          <VStack align="stretch" gap={1}>
            {payload.questions.map((q: string, i: number) => (
              <Text key={i} fontSize="xs" color="gray.600">
                • {q}
              </Text>
            ))}
          </VStack>
        )}

        {/* Actions */}
        {resolved ? (
          <Text fontSize="xs" color="gray.500" fontStyle="italic">
            ✓{" "}
            {resolvedOption === "CONFIRM_SCOPE"
              ? "Scope confirmed"
              : "Adjustments requested"}
          </Text>
        ) : (
          <HStack gap={3} pt={1}>
            <Button
              size="sm"
              colorScheme="green"
              onClick={() => handleAction("CONFIRM_SCOPE")}
              loading={isSubmitting}
            >
              <Icon as={FiCheck} mr={1} />
              Confirm
            </Button>
            <Button
              size="sm"
              colorScheme="orange"
              variant="outline"
              onClick={() => handleAction("ADJUST_SCOPE")}
              loading={isSubmitting}
            >
              <Icon as={FiEdit} mr={1} />
              Adjust
            </Button>
          </HStack>
        )}
      </VStack>
    </Box>
  )
}
