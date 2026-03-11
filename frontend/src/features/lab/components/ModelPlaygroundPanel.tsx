import { Box, Button, HStack, Icon, Text, VStack } from "@chakra-ui/react"
import { useState } from "react"
import { FiInfo, FiPlay, FiX } from "react-icons/fi"
import { Checkbox } from "@/components/ui/checkbox"
import { useModelInfo } from "../hooks"
import { useExplainModel, useModelPredict } from "../hooks/useExplainability"
import { FeatureImportanceChart } from "./FeatureImportanceChart"
import { PredictionExplanation } from "./PredictionExplanation"

interface ModelPlaygroundPanelProps {
  artifactId: string
  onClose: () => void
}

export function ModelPlaygroundPanel({
  artifactId,
  onClose,
}: ModelPlaygroundPanelProps) {
  const {
    data: modelInfo,
    isLoading: infoLoading,
    error: infoError,
  } = useModelInfo(artifactId)
  const predict = useModelPredict()
  const explain = useExplainModel()
  const [featureValues, setFeatureValues] = useState<Record<string, string>>({})
  const [includeExplanation, setIncludeExplanation] = useState(false)

  const handlePredict = () => {
    if (!modelInfo) return
    const numericValues: Record<string, number> = {}
    for (const col of modelInfo.feature_columns) {
      numericValues[col] = parseFloat(featureValues[col] || "0") || 0
    }
    predict.mutate({
      artifactId,
      featureValues: numericValues,
      includeExplanation,
    })
  }

  return (
    <Box
      bg="gray.800"
      borderRadius="lg"
      p={4}
      border="1px solid"
      borderColor="gray.700"
    >
      <VStack align="stretch" gap={4}>
        <HStack justify="space-between">
          <Text fontSize="sm" fontWeight="bold" color="gray.300">
            Model Playground
          </Text>
          <Button size="xs" variant="ghost" onClick={onClose}>
            <FiX />
          </Button>
        </HStack>

        {infoLoading && (
          <Text fontSize="sm" color="gray.500">
            Loading model info...
          </Text>
        )}

        {infoError && (
          <Text fontSize="sm" color="red.400">
            Failed to load model info
          </Text>
        )}

        {modelInfo && (
          <>
            {/* Model metadata */}
            <HStack gap={4} fontSize="xs" color="gray.400">
              <Text>
                Type:{" "}
                <Text as="span" color="blue.300">
                  {modelInfo.model_type}
                </Text>
              </Text>
              <Text>
                Task:{" "}
                <Text as="span" color="blue.300">
                  {modelInfo.task_type}
                </Text>
              </Text>
              <Text>
                Features:{" "}
                <Text as="span" color="blue.300">
                  {modelInfo.feature_columns.length}
                </Text>
              </Text>
            </HStack>

            {/* Feature inputs */}
            <VStack align="stretch" gap={2}>
              <Text fontSize="xs" fontWeight="bold" color="gray.400">
                Feature Values
              </Text>
              {modelInfo.feature_columns.map((col) => (
                <HStack key={col} gap={2}>
                  <Text
                    fontSize="xs"
                    color="gray.400"
                    w="150px"
                    flexShrink={0}
                    truncate
                  >
                    {col}
                  </Text>
                  <input
                    type="number"
                    step="any"
                    value={featureValues[col] || ""}
                    onChange={(e) =>
                      setFeatureValues((prev) => ({
                        ...prev,
                        [col]: e.target.value,
                      }))
                    }
                    placeholder="0"
                    style={{
                      padding: "4px 8px",
                      borderRadius: "4px",
                      border: "1px solid var(--chakra-colors-gray-600)",
                      background: "var(--chakra-colors-gray-900)",
                      color: "inherit",
                      fontSize: "12px",
                      width: "100%",
                    }}
                  />
                </HStack>
              ))}
            </VStack>

            {/* Explanation checkbox */}
            <Checkbox
              checked={includeExplanation}
              onCheckedChange={(checked) => setIncludeExplanation(!!checked)}
            >
              <Text fontSize="xs" color="gray.300">
                Include SHAP explanation
              </Text>
            </Checkbox>

            {/* Predict button */}
            <HStack gap={2}>
              <Button
                size="sm"
                colorScheme="blue"
                onClick={handlePredict}
                loading={predict.isPending}
              >
                <FiPlay style={{ marginRight: "4px" }} />
                Run Prediction
              </Button>
              <Button
                size="sm"
                variant="outline"
                colorScheme="purple"
                onClick={() => explain.mutate(artifactId)}
                loading={explain.isPending}
              >
                <Icon as={FiInfo} mr={1} />
                Explain Model
              </Button>
            </HStack>

            {/* Results */}
            {predict.data && (
              <Box
                bg="gray.900"
                p={3}
                borderRadius="md"
                border="1px solid"
                borderColor="gray.700"
              >
                <VStack align="stretch" gap={2}>
                  <Text fontSize="xs" fontWeight="bold" color="gray.400">
                    Prediction Result
                  </Text>
                  <HStack gap={4}>
                    <Text fontSize="sm" color="green.300" fontWeight="bold">
                      {predict.data.prediction_label ||
                        String(predict.data.prediction)}
                    </Text>
                    <Text fontSize="xs" color="gray.500">
                      ({predict.data.task_type})
                    </Text>
                  </HStack>
                  {predict.data.probabilities && (
                    <VStack align="stretch" gap={1}>
                      <Text fontSize="xs" color="gray.400">
                        Class Probabilities
                      </Text>
                      {Object.entries(predict.data.probabilities).map(
                        ([cls, prob]) => (
                          <HStack key={cls} gap={2} fontSize="xs">
                            <Text color="gray.400" w="80px">
                              {cls}
                            </Text>
                            <Box
                              flex={1}
                              bg="gray.700"
                              borderRadius="sm"
                              h="12px"
                              overflow="hidden"
                            >
                              <Box
                                bg="blue.400"
                                h="full"
                                w={`${(prob * 100).toFixed(1)}%`}
                              />
                            </Box>
                            <Text color="gray.400" w="50px" textAlign="right">
                              {(prob * 100).toFixed(1)}%
                            </Text>
                          </HStack>
                        ),
                      )}
                    </VStack>
                  )}
                </VStack>
              </Box>
            )}

            {predict.error && (
              <Text fontSize="sm" color="red.400">
                Prediction failed. Check model compatibility.
              </Text>
            )}

            {/* Explanation results */}
            {predict.data?.shap_values &&
              predict.data?.shap_base_value !== undefined && (
                <PredictionExplanation
                  shapValues={predict.data.shap_values}
                  baseValue={predict.data.shap_base_value}
                  prediction={
                    predict.data.prediction_label || predict.data.prediction
                  }
                />
              )}

            {explain.data?.supported && explain.data.feature_importance && (
              <FeatureImportanceChart
                features={explain.data.feature_importance}
              />
            )}

            {explain.data && !explain.data.supported && explain.data.reason && (
              <Text fontSize="sm" color="yellow.400">
                Explanation not available: {explain.data.reason}
              </Text>
            )}

            {explain.error && (
              <Text fontSize="sm" color="red.400">
                Failed to generate explanation
              </Text>
            )}
          </>
        )}
      </VStack>
    </Box>
  )
}
