import {
  Badge,
  Box,
  Button,
  Code,
  HStack,
  Text,
  VStack,
} from "@chakra-ui/react"
import { FiCheckCircle } from "react-icons/fi"

export interface BlueprintData {
  target: string
  features: string[]
  model_type: string
  task_type: string
  hyperparameters: Record<string, unknown>
  rationale: string
  estimated_training_time?: number
}

interface BlueprintCardProps {
  data: BlueprintData
  onApprove?: () => void
  isApproved?: boolean
}

export function BlueprintCard({
  data,
  onApprove,
  isApproved = false,
}: BlueprintCardProps) {
  return (
    <Box
      borderLeft="4px solid"
      borderLeftColor="blue.500"
      bg="gray.800"
      borderRadius="lg"
      p={4}
      border="1px solid"
      borderColor="gray.700"
    >
      <VStack align="stretch" gap={4}>
        {/* Header */}
        <VStack align="stretch" gap={2}>
          <HStack justify="space-between">
            <Text fontSize="lg" fontWeight="bold">
              Blueprint: {data.target}
            </Text>
            {isApproved && (
              <Badge
                colorScheme="green"
                display="flex"
                alignItems="center"
                gap={1}
              >
                <FiCheckCircle />
                Approved
              </Badge>
            )}
          </HStack>
          <Text fontSize="sm" color="gray.400">
            {data.task_type} • {data.model_type}
          </Text>
        </VStack>

        {/* Rationale */}
        <VStack align="stretch" gap={1}>
          <Text fontSize="sm" fontWeight="medium" color="gray.300">
            Rationale
          </Text>
          <Text fontSize="sm" color="gray.400">
            {data.rationale}
          </Text>
        </VStack>

        {/* Features */}
        <VStack align="stretch" gap={2}>
          <Text fontSize="sm" fontWeight="medium" color="gray.300">
            Features ({data.features.length})
          </Text>
          <HStack wrap="wrap" gap={2}>
            {data.features.map((feature) => (
              <Badge key={feature} colorScheme="purple" fontSize="xs">
                {feature}
              </Badge>
            ))}
          </HStack>
        </VStack>

        {/* Hyperparameters */}
        <VStack align="stretch" gap={1}>
          <Text fontSize="sm" fontWeight="medium" color="gray.300">
            Hyperparameters
          </Text>
          <Code
            fontSize="xs"
            p={2}
            borderRadius="md"
            bg="gray.900"
            overflowX="auto"
            whiteSpace="pre-wrap"
            wordBreak="break-word"
          >
            {JSON.stringify(data.hyperparameters, null, 2)}
          </Code>
        </VStack>

        {/* Training time and action button */}
        <HStack justify="space-between" align="center">
          {data.estimated_training_time && (
            <Text fontSize="xs" color="gray.500">
              Est. training time: {data.estimated_training_time}h
            </Text>
          )}
          <Button
            size="sm"
            colorScheme="blue"
            onClick={onApprove}
            disabled={isApproved}
            variant={isApproved ? "ghost" : "solid"}
          >
            {isApproved ? "Approved" : "Approve Blueprint"}
          </Button>
        </HStack>
      </VStack>
    </Box>
  )
}
