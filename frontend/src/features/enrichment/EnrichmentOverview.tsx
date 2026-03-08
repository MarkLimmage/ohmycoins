import {
  Box,
  Card,
  Heading,
  SimpleGrid,
  Spinner,
  Text,
  VStack,
} from "@chakra-ui/react"
import { useEnrichmentStats } from "./hooks"
import type { EnricherStat } from "./types"

function StatBox({
  label,
  value,
  color,
}: {
  label: string
  value: string | number
  color?: string
}) {
  return (
    <Box>
      <Text fontSize="xs" color="gray.500">
        {label}
      </Text>
      <Text fontSize="lg" fontWeight="bold" color={color}>
        {value}
      </Text>
    </Box>
  )
}

function EnricherCard({ enricher }: { enricher: EnricherStat }) {
  return (
    <Card.Root>
      <Card.Body>
        <VStack align="stretch" gap={3}>
          <Heading size="sm">{enricher.name}</Heading>
          <SimpleGrid columns={2} gap={3}>
            <StatBox label="Total Runs" value={enricher.total_runs} />
            <StatBox label="Items Enriched" value={enricher.items_enriched} />
            <StatBox
              label="Last Run"
              value={
                enricher.last_run
                  ? new Date(enricher.last_run).toLocaleString()
                  : "Never"
              }
            />
            <StatBox
              label="Avg Duration"
              value={`${enricher.avg_duration_secs.toFixed(1)}s`}
            />
          </SimpleGrid>
        </VStack>
      </Card.Body>
    </Card.Root>
  )
}

export function EnrichmentOverview() {
  const { data: stats, isLoading, error } = useEnrichmentStats()

  if (isLoading) {
    return (
      <Box textAlign="center" py={8}>
        <Spinner />
      </Box>
    )
  }

  if (error || !stats) {
    return (
      <Box textAlign="center" py={8}>
        <Text color="red.500">Failed to load enrichment stats</Text>
      </Box>
    )
  }

  const coverageColor =
    stats.coverage_pct >= 80
      ? "green.500"
      : stats.coverage_pct >= 50
        ? "yellow.500"
        : "red.500"

  return (
    <VStack align="stretch" gap={6}>
      <Heading size="md">Enrichment Coverage</Heading>

      <SimpleGrid columns={{ base: 2, md: 4 }} gap={4}>
        <Card.Root>
          <Card.Body>
            <StatBox label="Total News Items" value={stats.total_items} />
          </Card.Body>
        </Card.Root>
        <Card.Root>
          <Card.Body>
            <StatBox
              label="Enriched"
              value={stats.enriched_items}
              color="green.500"
            />
          </Card.Body>
        </Card.Root>
        <Card.Root>
          <Card.Body>
            <StatBox
              label="Unenriched"
              value={stats.unenriched_items}
              color="gray.500"
            />
          </Card.Body>
        </Card.Root>
        <Card.Root>
          <Card.Body>
            <StatBox
              label="Coverage"
              value={`${stats.coverage_pct}%`}
              color={coverageColor}
            />
          </Card.Body>
        </Card.Root>
      </SimpleGrid>

      {stats.by_enricher.length > 0 && (
        <>
          <Heading size="sm">Enrichers</Heading>
          <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} gap={4}>
            {stats.by_enricher.map((enricher) => (
              <EnricherCard key={enricher.name} enricher={enricher} />
            ))}
          </SimpleGrid>
        </>
      )}
    </VStack>
  )
}
