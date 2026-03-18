import {
  Box,
  Button,
  Heading,
  HStack,
  Icon,
  Text,
  VStack,
} from "@chakra-ui/react"
import type React from "react"
import { useState } from "react"
import { FiAlertCircle, FiCheck, FiEdit, FiX } from "react-icons/fi"
import { AgentService } from "../../../client"
import { useLabContext } from "../context/LabContext"
import type { ActionRequest } from "../types"

interface ActionRequestBannerProps {
  request: ActionRequest
}

export const ActionRequestBanner: React.FC<ActionRequestBannerProps> = ({
  request,
}) => {
  const { state, dispatch } = useLabContext()
  const [isSubmitting, setIsSubmitting] = useState(false)

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
      dispatch({ type: "CLEAR_ACTION" })
    } catch (error) {
      console.error("Failed to submit approval:", error)
      setIsSubmitting(false)
    }
  }

  return (
    <Box
      p={6}
      bg="orange.50"
      borderLeft="4px solid"
      borderColor="orange.500"
      borderRadius="md"
      boxShadow="md"
      my={4}
      _dark={{ bg: "orange.900" }}
    >
      <VStack align="start" gap={4}>
        <HStack>
          <Icon as={FiAlertCircle} color="orange.500" boxSize={6} />
          <Heading size="md" color="orange.700" _dark={{ color: "white" }}>
            Action Required
          </Heading>
        </HStack>

        <Text fontSize="lg" fontWeight="medium">
          {request.description}
        </Text>

        <HStack gap={4} pt={2}>
          {request.options.includes("APPROVE") && (
            <Button
              colorScheme="green"
              onClick={() => handleAction("APPROVE")}
              loading={isSubmitting}
            >
              <Icon as={FiCheck} mr={2} />
              Approve
            </Button>
          )}

          {request.options.includes("REJECT") && (
            <Button
              colorScheme="red"
              variant="outline"
              onClick={() => handleAction("REJECT")}
              loading={isSubmitting}
            >
              <Icon as={FiX} mr={2} />
              Reject
            </Button>
          )}

          {request.options.includes("EDIT_BLUEPRINT") && (
            <Button
              colorScheme="blue"
              variant="outline"
              onClick={() => handleAction("EDIT_BLUEPRINT")}
              loading={isSubmitting}
            >
              <Icon as={FiEdit} mr={2} />
              Edit Blueprint
            </Button>
          )}
        </HStack>
      </VStack>
    </Box>
  )
}
