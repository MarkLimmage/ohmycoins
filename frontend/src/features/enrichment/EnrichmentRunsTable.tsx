import { Box, Spinner, Table, Text, VStack } from "@chakra-ui/react"
import { useEnrichmentRuns } from "./hooks"
import type { EnrichmentRun } from "./types"

function StatusBadge({ status }: { status: string }) {
  const color =
    status === "completed"
      ? "green.500"
      : status === "failed"
        ? "red.500"
        : "yellow.500"
  return (
    <Text fontSize="sm" fontWeight="semibold" color={color}>
      {status}
    </Text>
  )
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "-"
  return new Date(dateStr).toLocaleString()
}

function RunRow({ run }: { run: EnrichmentRun }) {
  return (
    <Table.Row>
      <Table.Cell>{run.id}</Table.Cell>
      <Table.Cell>{run.enricher_name}</Table.Cell>
      <Table.Cell>
        <StatusBadge status={run.status} />
      </Table.Cell>
      <Table.Cell>{run.trigger}</Table.Cell>
      <Table.Cell>{run.items_processed}</Table.Cell>
      <Table.Cell>{run.items_enriched}</Table.Cell>
      <Table.Cell>{run.items_failed}</Table.Cell>
      <Table.Cell>{formatDate(run.completed_at)}</Table.Cell>
      <Table.Cell>
        {run.error_message ? (
          <Text fontSize="xs" color="red.400" maxW="200px" truncate>
            {run.error_message}
          </Text>
        ) : (
          "-"
        )}
      </Table.Cell>
    </Table.Row>
  )
}

export function EnrichmentRunsTable() {
  const { data, isLoading, error } = useEnrichmentRuns()

  if (isLoading) {
    return (
      <Box textAlign="center" py={8}>
        <Spinner />
      </Box>
    )
  }

  if (error || !data) {
    return (
      <Box textAlign="center" py={8}>
        <Text color="red.500">Failed to load enrichment runs</Text>
      </Box>
    )
  }

  if (data.runs.length === 0) {
    return (
      <Box textAlign="center" py={8}>
        <Text color="gray.500">No enrichment runs yet</Text>
      </Box>
    )
  }

  return (
    <VStack align="stretch" gap={3}>
      <Text fontSize="sm" color="gray.500">
        Showing {data.count} recent runs
      </Text>
      <Box overflowX="auto">
        <Table.Root size="sm" variant="outline">
          <Table.Header>
            <Table.Row>
              <Table.ColumnHeader>ID</Table.ColumnHeader>
              <Table.ColumnHeader>Enricher</Table.ColumnHeader>
              <Table.ColumnHeader>Status</Table.ColumnHeader>
              <Table.ColumnHeader>Trigger</Table.ColumnHeader>
              <Table.ColumnHeader>Processed</Table.ColumnHeader>
              <Table.ColumnHeader>Enriched</Table.ColumnHeader>
              <Table.ColumnHeader>Failed</Table.ColumnHeader>
              <Table.ColumnHeader>Completed</Table.ColumnHeader>
              <Table.ColumnHeader>Error</Table.ColumnHeader>
            </Table.Row>
          </Table.Header>
          <Table.Body>
            {data.runs.map((run) => (
              <RunRow key={run.id} run={run} />
            ))}
          </Table.Body>
        </Table.Root>
      </Box>
    </VStack>
  )
}
