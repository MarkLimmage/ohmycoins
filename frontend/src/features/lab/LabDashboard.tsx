import {
  Box,
  Button,
  Flex,
  Heading,
  HStack,
  Text,
  VStack,
} from "@chakra-ui/react"
import { useEffect, useState } from "react"
import { FiPlus } from "react-icons/fi"
import { OpenAPI } from "@/client"
import AgentTerminal from "@/components/Lab/AgentTerminal"
import { type Artifact, ArtifactViewer } from "./components/ArtifactViewer"
import { BlueprintCard, type BlueprintData } from "./components/BlueprintCard"
import { ModelPlaygroundPanel } from "./components/ModelPlaygroundPanel"
import { type PromoteFormData, PromoteModal } from "./components/PromoteModal"
import { SessionCreateForm } from "./components/SessionCreateForm"
import { SessionList } from "./components/SessionList"
import {
  type TrainingMetric,
  TrainingProgressChart,
} from "./components/TrainingProgressChart"
import {
  useCancelSession,
  useDeleteSession,
  useLabSessions,
  usePromoteArtifact,
  useSessionArtifacts,
} from "./hooks"
import { useLabWebSocket } from "./hooks/useLabWebSocket"

export function LabDashboard() {
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(
    null,
  )
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [resolvedToken, setResolvedToken] = useState<string | undefined>()
  const [blueprintData, setBlueprintData] = useState<BlueprintData | null>(null)
  const [trainingMetrics, setTrainingMetrics] = useState<TrainingMetric[]>([])
  const [approvedBlueprints, setApprovedBlueprints] = useState<Set<string>>(
    new Set(),
  )
  const [promoteModalOpen, setPromoteModalOpen] = useState(false)
  const [promoteArtifactState, setPromoteArtifactState] =
    useState<Artifact | null>(null)
  const [playgroundArtifact, setPlaygroundArtifact] = useState<Artifact | null>(
    null,
  )

  const { data: sessionsData } = useLabSessions()
  const { data: artifactsData } = useSessionArtifacts(selectedSessionId)
  const cancelSession = useCancelSession()
  const deleteSession = useDeleteSession()
  const promoteArtifact = usePromoteArtifact()

  const artifacts: Artifact[] = (artifactsData || []).map((a) => ({
    id: a.id,
    name: a.name,
    path: a.file_path || "",
    type: (["model", "data", "report"].includes(a.artifact_type)
      ? a.artifact_type
      : "other") as Artifact["type"],
    size: a.size_bytes || undefined,
  }))

  // Resolve token once on mount
  useEffect(() => {
    const resolveToken = async () => {
      const rawToken = OpenAPI.TOKEN
      if (typeof rawToken === "function") {
        try {
          const token = await (rawToken as () => Promise<string>)()
          setResolvedToken(token)
        } catch (err) {
          console.error("Failed to resolve token:", err)
        }
      } else {
        setResolvedToken(rawToken)
      }
    }
    resolveToken()
  }, [])

  const { messages } = useLabWebSocket({
    sessionId: selectedSessionId,
    enabled: !!selectedSessionId,
  })

  // Process messages to extract blueprint, metrics, and artifacts
  useEffect(() => {
    messages.forEach((msg) => {
      if (msg.type === "blueprint" && msg.metadata) {
        try {
          const blueprint = JSON.parse(msg.content) as BlueprintData
          setBlueprintData(blueprint)
        } catch (err) {
          console.error("Failed to parse blueprint:", err)
        }
      } else if (msg.type === "metric" && msg.metadata) {
        try {
          const metric = JSON.parse(msg.content) as TrainingMetric
          setTrainingMetrics((prev) => {
            // Update or add metric
            const updated = prev.filter((m) => m.name !== metric.name)
            return [...updated, metric]
          })
        } catch (err) {
          console.error("Failed to parse metric:", err)
        }
      }
    })
  }, [messages])

  const selectedSession = sessionsData?.data?.find(
    (s) => s.id === selectedSessionId,
  )
  const isActive =
    selectedSession?.status === "pending" ||
    selectedSession?.status === "running"

  const baseUrl =
    OpenAPI.BASE?.replace(/^http/, "ws") || "wss://api.ohmycoins.com"
  const streamUrl =
    selectedSessionId && resolvedToken
      ? `${baseUrl}/ws/agent/${selectedSessionId}/stream?token=${resolvedToken}`
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
            onDelete={(id) => {
              deleteSession.mutate(id)
              if (id === selectedSessionId) {
                setSelectedSessionId(null)
              }
            }}
          />
        </Box>

        {/* Right panel: Terminal and outputs */}
        <Box flex={1} minH="500px">
          {selectedSessionId ? (
            <VStack align="stretch" gap={4}>
              <AgentTerminal
                sessionId={selectedSessionId}
                streamUrl={streamUrl}
                allowInteraction={isActive}
                onCancel={isActive ? handleCancel : undefined}
              />

              {/* Blueprint Card */}
              {blueprintData && (
                <BlueprintCard
                  data={blueprintData}
                  onApprove={() => {
                    setApprovedBlueprints((prev) => {
                      const next = new Set(prev)
                      next.add(blueprintData.target)
                      return next
                    })
                  }}
                  isApproved={approvedBlueprints.has(blueprintData.target)}
                />
              )}

              {/* Training Progress */}
              {trainingMetrics.length > 0 && (
                <TrainingProgressChart metrics={trainingMetrics} />
              )}

              {/* Artifacts */}
              {artifacts.length > 0 && (
                <ArtifactViewer
                  artifacts={artifacts}
                  onPromote={(artifact) => {
                    setPromoteArtifactState(artifact)
                    setPromoteModalOpen(true)
                  }}
                  onTest={setPlaygroundArtifact}
                />
              )}

              {/* Model Playground */}
              {playgroundArtifact?.id && (
                <ModelPlaygroundPanel
                  artifactId={playgroundArtifact.id}
                  onClose={() => setPlaygroundArtifact(null)}
                />
              )}
            </VStack>
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

      {/* Promote Modal */}
      <PromoteModal
        isOpen={promoteModalOpen}
        onClose={() => {
          setPromoteModalOpen(false)
          setPromoteArtifactState(null)
        }}
        artifactName={promoteArtifactState?.name}
        onSubmit={(data: PromoteFormData) => {
          if (!promoteArtifactState?.id) return
          const freqMap: Record<string, number> = {
            "1h": 3600,
            "4h": 14400,
            "12h": 43200,
            "24h": 86400,
          }
          promoteArtifact.mutate({
            artifactId: promoteArtifactState.id,
            algorithmName: data.algorithm_name,
            description: data.description,
            positionLimit: data.position_limit,
            dailyLossLimit: data.daily_loss_limit,
            executionFrequency: freqMap[data.execution_frequency] || 14400,
          })
          setPromoteModalOpen(false)
          setPromoteArtifactState(null)
        }}
      />
    </VStack>
  )
}
