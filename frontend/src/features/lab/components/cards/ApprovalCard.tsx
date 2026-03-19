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
import { FiCheck, FiEdit, FiFileText, FiX } from "react-icons/fi"
import { AgentService } from "../../../../client"
import { useLabContext } from "../../context/LabContext"
import type { LabEventPayload } from "../../types"

interface ApprovalCardProps {
  messageId: string
  payload: LabEventPayload
  resolved?: boolean
  resolvedOption?: string
}

export const ApprovalCard: React.FC<ApprovalCardProps> = ({
  messageId,
  payload,
  resolved,
  resolvedOption,
}) => {
  const { state, dispatch } = useLabContext()
  const [isSubmitting, setIsSubmitting] = useState(false)
  const context = payload.context || {}

  const handleAction = async (option: string) => {
    if (!state.sessionId) return
    setIsSubmitting(true)
    try {
      await AgentService.approveRequest({
        sessionId: state.sessionId,
        requestBody: {
          approved: option === "APPROVE",
          reason: option === "APPROVE" ? undefined : option,
        },
      })
      dispatch({
        type: "RESOLVE_ACTION",
        payload: { messageId, option },
      })
    } catch (error) {
      console.error("Failed to submit approval:", error)
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
          <Icon as={FiFileText} color={resolved ? "gray.500" : "orange.500"} />
          <Heading size="sm" color={resolved ? "gray.600" : "orange.700"}>
            Approval Required
          </Heading>
        </Flex>

        <Text fontSize="sm">{payload.description}</Text>

        {/* Blueprint Context */}
        {Object.keys(context).length > 0 && (
          <Box
            bg="white"
            p={3}
            borderRadius="md"
            border="1px solid"
            borderColor="gray.200"
          >
            {context.features && (
              <Text fontSize="xs" mb={1}>
                <strong>Features:</strong> {context.features.join(", ")}
              </Text>
            )}
            {context.algorithm && (
              <Text fontSize="xs" mb={1}>
                <strong>Algorithm:</strong> {context.algorithm}
              </Text>
            )}
            {context.estimated_time && (
              <Text fontSize="xs">
                <strong>Est. Time:</strong> {context.estimated_time}
              </Text>
            )}
          </Box>
        )}

        {/* Actions */}
        {resolved ? (
          <Text fontSize="xs" color="gray.500" fontStyle="italic">
            ✓{" "}
            {resolvedOption === "APPROVE"
              ? "Approved"
              : resolvedOption === "REJECT"
                ? "Rejected"
                : "Edit requested"}
          </Text>
        ) : (
          <HStack gap={3} pt={1}>
            <Button
              size="sm"
              colorScheme="green"
              onClick={() => handleAction("APPROVE")}
              loading={isSubmitting}
            >
              <Icon as={FiCheck} mr={1} />
              Approve
            </Button>
            <Button
              size="sm"
              colorScheme="red"
              variant="outline"
              onClick={() => handleAction("REJECT")}
              loading={isSubmitting}
            >
              <Icon as={FiX} mr={1} />
              Reject
            </Button>
            {payload.options?.includes("EDIT_BLUEPRINT") && (
              <Button
                size="sm"
                colorScheme="blue"
                variant="outline"
                onClick={() => handleAction("EDIT_BLUEPRINT")}
                loading={isSubmitting}
              >
                <Icon as={FiEdit} mr={1} />
                Edit Blueprint
              </Button>
            )}
          </HStack>
        )}
      </VStack>
    </Box>
  )
}
