import {
  Badge,
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
import { FiBarChart2, FiCheck } from "react-icons/fi"
import { AgentService } from "../../../../client"
import { useLabContext } from "../../context/LabContext"
import type { LabEventPayload } from "../../types"

interface ModelSelectionCardProps {
  messageId: string
  payload: LabEventPayload
  resolved?: boolean
  resolvedOption?: string
}

interface ModelInfo {
  name: string
  accuracy?: number
  f1_score?: number
  training_time?: number
  pros?: string[]
  cons?: string[]
}

export const ModelSelectionCard: React.FC<ModelSelectionCardProps> = ({
  messageId,
  payload,
  resolved,
  resolvedOption,
}) => {
  const { state, dispatch } = useLabContext()
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [selectedModel, setSelectedModel] = useState<string | null>(
    payload.recommendation?.model || null,
  )

  const models: ModelInfo[] = payload.models || []
  const recommendation = payload.recommendation

  const handleSelect = async () => {
    if (!state.sessionId || !selectedModel) return
    setIsSubmitting(true)
    try {
      await AgentService.selectChoice({
        sessionId: state.sessionId,
        requestBody: { selected_model: selectedModel },
      })
      dispatch({
        type: "RESOLVE_ACTION",
        payload: { messageId, option: `Selected: ${selectedModel}` },
      })
    } catch (error) {
      console.error("Failed to select model:", error)
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
          <Icon as={FiBarChart2} color={resolved ? "gray.500" : "orange.500"} />
          <Heading size="sm" color={resolved ? "gray.600" : "orange.700"}>
            Model Selection
          </Heading>
        </Flex>

        <Text fontSize="sm">{payload.description}</Text>

        {/* Model Cards */}
        {models.map((model) => (
          <Box
            key={model.name}
            p={3}
            bg={selectedModel === model.name && !resolved ? "blue.50" : "white"}
            border="2px solid"
            borderColor={
              selectedModel === model.name && !resolved
                ? "blue.400"
                : "gray.200"
            }
            borderRadius="md"
            cursor={resolved ? "default" : "pointer"}
            onClick={() => !resolved && setSelectedModel(model.name)}
            _hover={resolved ? {} : { borderColor: "blue.300" }}
          >
            <Flex justify="space-between" align="center" mb={1}>
              <Text fontWeight="bold" fontSize="sm">
                {model.name}
              </Text>
              {recommendation?.model === model.name && (
                <Badge colorPalette="green" size="sm">
                  Recommended
                </Badge>
              )}
            </Flex>
            <HStack gap={4} mb={2}>
              {model.accuracy != null && (
                <Text fontSize="xs" color="gray.600">
                  Accuracy: {(model.accuracy * 100).toFixed(1)}%
                </Text>
              )}
              {model.f1_score != null && (
                <Text fontSize="xs" color="gray.600">
                  F1: {(model.f1_score * 100).toFixed(1)}%
                </Text>
              )}
              {model.training_time != null && (
                <Text fontSize="xs" color="gray.600">
                  Training: {model.training_time}s
                </Text>
              )}
            </HStack>
            {model.pros && (
              <Text fontSize="xs" color="green.600">
                + {model.pros.join(", ")}
              </Text>
            )}
            {model.cons && (
              <Text fontSize="xs" color="red.600">
                - {model.cons.join(", ")}
              </Text>
            )}
          </Box>
        ))}

        {/* Actions */}
        {resolved ? (
          <Text fontSize="xs" color="gray.500" fontStyle="italic">
            ✓ {resolvedOption}
          </Text>
        ) : (
          <HStack gap={3} pt={1}>
            <Button
              size="sm"
              colorScheme="blue"
              onClick={handleSelect}
              loading={isSubmitting}
              disabled={!selectedModel}
            >
              <Icon as={FiCheck} mr={1} />
              Select Model
            </Button>
          </HStack>
        )}
      </VStack>
    </Box>
  )
}
