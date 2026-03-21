import { Box, Flex, Heading, HStack, VStack } from "@chakra-ui/react"
import { useState } from "react"
import { SessionDrawer } from "./components/SessionDrawer"
import { LabProvider } from "./context/LabContext"
import { useDeleteSession, useLabSessions } from "./hooks"
import { LabSessionView } from "./LabSessionView"

export function LabDashboard() {
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(
    null,
  )
  const [drawerOpen, setDrawerOpen] = useState(false)

  const { data: sessionsData } = useLabSessions()
  const deleteSession = useDeleteSession()

  return (
    <VStack align="stretch" gap={2}>
      <HStack justify="space-between">
        <HStack gap={3}>
          <SessionDrawer
            sessions={sessionsData?.data || []}
            selectedId={selectedSessionId}
            onSelect={setSelectedSessionId}
            onDelete={(id) => {
              deleteSession.mutate(id)
              if (id === selectedSessionId) {
                setSelectedSessionId(null)
              }
            }}
            open={drawerOpen}
            onOpenChange={setDrawerOpen}
          />
          <Heading size="lg">The Lab</Heading>
        </HStack>
      </HStack>

      <Box flex={1} minH="500px">
        {selectedSessionId ? (
          <LabProvider sessionId={selectedSessionId}>
            <LabSessionView />
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
            minH="500px"
          >
            <VStack gap={3} color="gray.500">
              <Flex fontSize="lg">No session selected</Flex>
              <Flex fontSize="sm">
                Select a session from the list or create a new one
              </Flex>
            </VStack>
          </Flex>
        )}
      </Box>
    </VStack>
  )
}
