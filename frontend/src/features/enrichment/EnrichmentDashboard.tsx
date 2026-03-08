import {
  Button,
  Container,
  Heading,
  HStack,
  Text,
  VStack,
} from "@chakra-ui/react"
import { EnrichmentOverview } from "./EnrichmentOverview"
import { EnrichmentRunsTable } from "./EnrichmentRunsTable"
import { useTriggerEnrichment } from "./hooks"

export function EnrichmentDashboard() {
  const triggerEnrichment = useTriggerEnrichment()

  const handleTrigger = () => {
    triggerEnrichment.mutate({ enricher: "all", limit: 100 })
  }

  return (
    <Container maxW="full" py={8}>
      <VStack align="stretch" gap={8}>
        <VStack align="flex-start" gap={4}>
          <Heading size="lg">Enrichment Dashboard</Heading>
          <HStack>
            <Button
              onClick={handleTrigger}
              loading={triggerEnrichment.isPending}
              loadingText="Running..."
              colorScheme="blue"
              size="md"
            >
              Run Enrichment
            </Button>
            {triggerEnrichment.isSuccess && (
              <Text fontSize="sm" color="green.600">
                Queued {triggerEnrichment.data?.items_queued || 0} items
              </Text>
            )}
            {triggerEnrichment.isError && (
              <Text fontSize="sm" color="red.600">
                Error triggering enrichment
              </Text>
            )}
          </HStack>
        </VStack>

        <VStack align="stretch" gap={6}>
          <EnrichmentOverview />
        </VStack>

        <VStack align="stretch" gap={6}>
          <Heading size="md">Recent Runs</Heading>
          <EnrichmentRunsTable />
        </VStack>
      </VStack>
    </Container>
  )
}
