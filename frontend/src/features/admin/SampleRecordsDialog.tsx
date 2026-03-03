import { Box, Spinner, Table, Text } from "@chakra-ui/react"
import {
  DialogBody,
  DialogCloseTrigger,
  DialogContent,
  DialogHeader,
  DialogRoot,
  DialogTitle,
} from "@/components/ui/dialog"
import { useSampleRecords } from "./hooks"

interface SampleRecordsDialogProps {
  instanceId: string | null
  pluginName: string
  open: boolean
  onOpenChange: (open: boolean) => void
}

function formatCell(value: unknown, column: string): string {
  if (value == null) return "-"
  if (
    typeof value === "string" &&
    (column.endsWith("_at") || column === "timestamp")
  ) {
    try {
      return new Date(value).toLocaleString()
    } catch {
      return value
    }
  }
  if (Array.isArray(value)) return value.join(", ")
  if (typeof value === "number") return value.toLocaleString()
  const str = String(value)
  return str.length > 80 ? `${str.slice(0, 80)}...` : str
}

export const SampleRecordsDialog = ({
  instanceId,
  pluginName,
  open,
  onOpenChange,
}: SampleRecordsDialogProps) => {
  const { data, isLoading, error } = useSampleRecords(open ? instanceId : null)

  return (
    <DialogRoot
      size="xl"
      open={open}
      onOpenChange={(e) => onOpenChange(e.open)}
    >
      <DialogContent maxW="900px">
        <DialogHeader>
          <DialogTitle>{pluginName} - Sample Records</DialogTitle>
        </DialogHeader>
        <DialogCloseTrigger />
        <DialogBody>
          {isLoading && (
            <Box textAlign="center" py={8}>
              <Spinner size="lg" />
            </Box>
          )}

          {error && (
            <Text color="red.500">
              Failed to load records: {(error as Error).message}
            </Text>
          )}

          {data && (
            <>
              <Text fontSize="sm" color="gray.500" mb={3}>
                {data.data_type} — Showing {data.records.length} of{" "}
                {data.total_count.toLocaleString()} records
              </Text>

              {data.records.length === 0 ? (
                <Box textAlign="center" py={6} bg="gray.50" borderRadius="md">
                  <Text color="gray.500">No records collected yet.</Text>
                </Box>
              ) : (
                <Box overflowX="auto">
                  <Table.Root size="sm" variant="outline">
                    <Table.Header>
                      <Table.Row>
                        {data.columns.map((col) => (
                          <Table.ColumnHeader key={col}>
                            {col.replace(/_/g, " ")}
                          </Table.ColumnHeader>
                        ))}
                      </Table.Row>
                    </Table.Header>
                    <Table.Body>
                      {data.records.map((record, idx) => (
                        <Table.Row key={idx}>
                          {data.columns.map((col) => (
                            <Table.Cell key={col} fontSize="xs">
                              {formatCell(record[col], col)}
                            </Table.Cell>
                          ))}
                        </Table.Row>
                      ))}
                    </Table.Body>
                  </Table.Root>
                </Box>
              )}
            </>
          )}
        </DialogBody>
      </DialogContent>
    </DialogRoot>
  )
}
