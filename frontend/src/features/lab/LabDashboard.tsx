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
import { getWebSocketBaseUrl } from "@/utils/env"

import { LabProvider } from "./context/LabContext"
import { LabSessionView } from "./LabSessionView"

export function LabDashboard() {
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(
    null,
  )
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [resolvedToken, setResolvedToken] = useState<string | undefined>()
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

  /* Logic moved to LabContext */

  const selectedSession = sessionsData?.data?.find(
    (s) => s.id === selectedSessionId,
  )
  const isActive =
    selectedSession?.status === "pending" ||
    selectedSession?.status === "running"

  const baseUrl = getWebSocketBaseUrl()
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
            <LabProvider sessionId={selectedSessionId}>
              <LabSessionView 
                onPromote={(artifact) => {
                  setPromoteArtifactState(artifact)
                  setPromoteModalOpen(true)
                }}
                onTest={setPlaygroundArtifact}
                playgroundArtifact={playgroundArtifact}
                setPlaygroundArtifact={setPlaygroundArtifact}
                approvedBlueprints={approvedBlueprints}
                setApprovedBlueprints={setApprovedBlueprints}
                artifacts={artifacts}
              />
            </LabProvider>
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
