import { Box, Button, HStack, Icon, Text, VStack } from "@chakra-ui/react"
import { FiDownload, FiInfo, FiPlay, FiUpload } from "react-icons/fi"

export interface Artifact {
  id?: string
  name: string
  path: string
  type: "model" | "data" | "report" | "other"
  size?: number
}

interface ArtifactViewerProps {
  artifacts: Artifact[]
  onPromote?: (artifact: Artifact) => void
  onTest?: (artifact: Artifact) => void
  onExplain?: (artifact: Artifact) => void
}

function getTypeColor(type: string): string {
  const colors: Record<string, string> = {
    model: "blue",
    data: "green",
    report: "purple",
    other: "gray",
  }
  return colors[type] || "gray"
}

function formatSize(bytes?: number): string {
  if (!bytes) return "—"
  if (bytes < 1024) return `${bytes}B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)}MB`
}

export function ArtifactViewer({
  artifacts,
  onPromote,
  onTest,
  onExplain,
}: ArtifactViewerProps) {
  return (
    <Box
      bg="gray.800"
      borderRadius="lg"
      p={4}
      border="1px solid"
      borderColor="gray.700"
    >
      <VStack align="stretch" gap={3}>
        <Text fontSize="sm" fontWeight="bold" color="gray.300">
          Artifacts ({artifacts.length})
        </Text>

        {artifacts.length === 0 ? (
          <Text fontSize="sm" color="gray.500">
            No artifacts generated yet
          </Text>
        ) : (
          <VStack align="stretch" gap={2}>
            {artifacts.map((artifact) => (
              <HStack
                key={artifact.path}
                p={3}
                bg="gray.900"
                borderRadius="md"
                border="1px solid"
                borderColor="gray.700"
                justify="space-between"
              >
                <VStack align="start" gap={1} flex={1}>
                  <HStack gap={2}>
                    <Text
                      fontSize="xs"
                      fontWeight="bold"
                      color={`${getTypeColor(artifact.type)}.400`}
                      textTransform="uppercase"
                    >
                      {artifact.type}
                    </Text>
                    <Text fontSize="sm" fontWeight="medium">
                      {artifact.name}
                    </Text>
                  </HStack>
                  <HStack gap={2} fontSize="xs" color="gray.500">
                    <Text>{artifact.path}</Text>
                    {artifact.size && (
                      <>
                        <Text>•</Text>
                        <Text>{formatSize(artifact.size)}</Text>
                      </>
                    )}
                  </HStack>
                </VStack>

                <HStack gap={2}>
                  <Button size="xs" variant="ghost" fontSize="xs">
                    <Icon as={FiDownload} mr={1} />
                    Download
                  </Button>
                  {artifact.type === "model" && onTest && (
                    <Button
                      size="xs"
                      variant="ghost"
                      colorScheme="green"
                      onClick={() => onTest(artifact)}
                      fontSize="xs"
                    >
                      <Icon as={FiPlay} mr={1} />
                      Test
                    </Button>
                  )}
                  {artifact.type === "model" && onExplain && (
                    <Button
                      size="xs"
                      variant="ghost"
                      colorScheme="purple"
                      onClick={() => onExplain(artifact)}
                      fontSize="xs"
                    >
                      <Icon as={FiInfo} mr={1} />
                      Explain
                    </Button>
                  )}
                  {artifact.type === "model" && onPromote && (
                    <Button
                      size="xs"
                      colorScheme="blue"
                      onClick={() => onPromote(artifact)}
                      fontSize="xs"
                    >
                      <Icon as={FiUpload} mr={1} />
                      Promote
                    </Button>
                  )}
                </HStack>
              </HStack>
            ))}
          </VStack>
        )}
      </VStack>
    </Box>
  )
}
